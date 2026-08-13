import os
import json
import time
from datetime import datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, text

from api.access_control import require_athlete_access
from api.dependencies import current_user, require_coach
from api.schemas import ActivityFeedbackPayload
from core.auth_service import AuthService
from core.training.activity_analysis_service import ActivityAnalysisService
from repositories.integration_repository import IntegrationRepository
from models.external_integration import ExternalIntegration
from models.imported_activity import ImportedActivity
from models.training import Training
from models.training_session import TrainingSession
from repositories.activity_repository import ActivityRepository
from repositories.activity_feedback_repository import ActivityFeedbackRepository
from repositories.access_repository import AccessRepository
from database.database import SessionLocal
from models.activity_feedback import ActivityFeedback


router = APIRouter(prefix="/integrations", tags=["integrations"])
repository = IntegrationRepository()
activities = ActivityRepository()
feedbacks = ActivityFeedbackRepository()
access = AccessRepository()

class ActivityTrainingSessionPayload(BaseModel):
    training_session_id: int | None = None


DEFAULT_STRAVA_REDIRECT_URI = (
    "https://api.runcoreapp.com.br"
    "/api/integrations/strava/callback"
)


def strava_redirect_uri():
    return (
        os.getenv("STRAVA_REDIRECT_URI")
        or DEFAULT_STRAVA_REDIRECT_URI
    )


def strava_configured():
    return bool(
        os.getenv("STRAVA_CLIENT_ID")
        and os.getenv("STRAVA_CLIENT_SECRET")
        and strava_redirect_uri()
    )


def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


def strava_request(url, token):
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            message = json.loads(body).get("message") or body
        except json.JSONDecodeError:
            message = body
        raise HTTPException(status_code=502, detail=f"Strava respondeu {exc.code}: {message[:180]}")


def refresh_strava_token(integration):
    if integration.expires_at > int(time.time()) + 60:
        return integration

    form = urlencode({"client_id": os.environ["STRAVA_CLIENT_ID"], "client_secret": os.environ["STRAVA_CLIENT_SECRET"], "refresh_token": integration.refresh_token, "grant_type": "refresh_token"}).encode()
    request = Request("https://www.strava.com/oauth/token", data=form, method="POST")
    with urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode())
    integration.access_token = result["access_token"]
    integration.refresh_token = result["refresh_token"]
    integration.expires_at = result["expires_at"]
    return repository.save(integration)


@router.get("/strava/status")
def strava_status(user=Depends(current_user)):
    integration = repository.get(user.id, "strava")
    return {"configured": strava_configured(), "connected": bool(integration and integration.active)}


@router.get("/strava/connect")
def connect_strava(user=Depends(current_user)):
    if not strava_configured():
        raise HTTPException(status_code=503, detail="A integração Strava ainda não foi configurada pelo administrador.")
    state = AuthService.create_token(user.id)
    query = urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "redirect_uri": strava_redirect_uri(),
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "activity:read_all",
        "state": state,
    })
    return {"authorization_url": f"https://www.strava.com/oauth/authorize?{query}"}


@router.get("/strava/callback")
def strava_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    scope: str = Query(default=""),
):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    if error or not code or not state:
        return RedirectResponse(f"{frontend_url}/?strava=cancelled")

    payload = AuthService.read_token(state)
    if payload is None:
        return RedirectResponse(f"{frontend_url}/?strava=invalid_state")

    form = urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": strava_redirect_uri(),
    }).encode()

    try:
        request = Request(
            "https://www.strava.com/oauth/token",
            data=form,
            method="POST",
        )
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode())
    except Exception:
        return RedirectResponse(f"{frontend_url}/?strava=failed")

    integration = repository.get(payload["sub"], "strava")
    if integration is None:
        integration = ExternalIntegration(
            user_id=payload["sub"],
            provider="strava",
            external_user_id=str(result["athlete"]["id"]),
        )

    integration.access_token = result["access_token"]
    integration.refresh_token = result["refresh_token"]
    integration.expires_at = result["expires_at"]
    integration.scopes = scope
    integration.active = True
    repository.save(integration)

    return RedirectResponse(f"{frontend_url}/?strava=connected")


@router.get("/strava/activities")
def list_strava_activities(user=Depends(current_user)):
    integration = repository.get(user.id, "strava")
    if integration is None or not integration.active:
        raise HTTPException(status_code=404, detail="Conta Strava não conectada.")
    return activities.list_for_integration(integration.id)


@router.put(
    "/strava/activities/{activity_id}/training-session"
)
def update_activity_training_session(
    activity_id: int,
    payload: ActivityTrainingSessionPayload,
    user=Depends(current_user),
):
    integration = repository.get(
        user.id,
        "strava",
    )

    if integration is None or not integration.active:
        raise HTTPException(
            status_code=404,
            detail="Conta Strava não conectada.",
        )

    activity = activities.get_for_integration(
        activity_id,
        integration.id,
    )

    if activity is None:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada.",
        )

    athlete_id = access.athlete_for_student(
        user.id,
    )

    if athlete_id is None:
        raise HTTPException(
            status_code=404,
            detail="Perfil de atleta não encontrado.",
        )

    with SessionLocal() as session:
        managed_activity = session.get(
            ImportedActivity,
            activity.id,
        )

        if managed_activity is None:
            raise HTTPException(
                status_code=404,
                detail="Atividade não encontrada.",
            )

        target_session_id = (
            payload.training_session_id
        )

        if target_session_id is None:
            managed_activity.training_session_id = None
            session.commit()

            return {
                "activity_id": managed_activity.id,
                "training_session_id": None,
                "message": (
                    "Vínculo com o treino removido."
                ),
            }

        training_session = session.scalar(
            select(TrainingSession)
            .join(
                Training,
                Training.id
                == TrainingSession.training_id,
            )
            .where(
                TrainingSession.id
                == target_session_id,
                Training.athlete_id == athlete_id,
            )
        )

        if training_session is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "A sessão selecionada não pertence "
                    "ao atleta conectado."
                ),
            )

        linked_activity = session.scalar(
            select(ImportedActivity)
            .where(
                ImportedActivity.training_session_id
                == target_session_id,
                ImportedActivity.id
                != managed_activity.id,
            )
        )

        if linked_activity is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A sessão selecionada já está vinculada "
                    "a outra atividade."
                ),
            )

        managed_activity.training_session_id = (
            training_session.id
        )

        session.commit()

        return {
            "activity_id": managed_activity.id,
            "training_session_id": (
                managed_activity.training_session_id
            ),
            "message": (
                "Atividade vinculada ao treino "
                "selecionado."
            ),
        }


@router.get("/strava/activities/{activity_id}/details")
def strava_activity_details(activity_id: int, user=Depends(current_user)):
    integration = repository.get(user.id, "strava")
    if integration is None or not integration.active:
        raise HTTPException(status_code=404, detail="Conta Strava não conectada.")

    activity = activities.get_for_integration(activity_id, integration.id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    try:
        integration = refresh_strava_token(integration)
        detail = strava_request(
            f"https://www.strava.com/api/v3/activities/{activity.provider_activity_id}",
            integration.access_token,
        )
        laps = strava_request(
            f"https://www.strava.com/api/v3/activities/{activity.provider_activity_id}/laps",
            integration.access_token,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Não foi possível carregar os detalhes da atividade no Strava.")

    def kilometers(value):
        return round((value or 0) / 1000, 3)

    activity_feedback = feedbacks.get_for_activity(
        activity.id,
    )

    analysis = ActivityAnalysisService.analyse(
        activity,
        laps,
        activity_feedback,
    )

    return {
        "analysis": analysis,
        "average_heartrate": detail.get("average_heartrate"),
        "max_heartrate": detail.get("max_heartrate"),
        "total_elevation_gain": detail.get("total_elevation_gain"),
        "average_cadence": detail.get("average_cadence"),
        "max_cadence": activity.max_cadence,
        "average_speed": detail.get("average_speed"),
        "max_speed": detail.get("max_speed"),
        "elapsed_time": detail.get("elapsed_time"),
        "laps": [
            {
                "number": index + 1,
                "distance": kilometers(lap.get("distance")),
                "moving_time": lap.get("moving_time", 0),
                "average_speed": lap.get("average_speed"),
                "average_heartrate": lap.get("average_heartrate"),
                "elevation_gain": lap.get("total_elevation_gain"),
            }
            for index, lap in enumerate(laps)
        ],
    }


def serialize_feedback(item):
    if item is None:
        return None
    return {
        "perceived_effort": item.perceived_effort,
        "feeling": item.feeling,
        "pain": item.pain,
        "sleep_quality": item.sleep_quality,
        "pre_fatigue": item.pre_fatigue,
        "notes": item.notes,
        "updated_at": item.updated_at,
    }


@router.get("/strava/activities/{activity_id}/feedback")
def get_activity_feedback(activity_id: int, user=Depends(current_user)):
    integration = repository.get(user.id, "strava")
    if integration is None or not integration.active:
        raise HTTPException(status_code=404, detail="Conta Strava não conectada.")
    activity = activities.get_for_integration(activity_id, integration.id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    return serialize_feedback(feedbacks.get_for_activity(activity.id))


@router.put("/strava/activities/{activity_id}/feedback")
def save_activity_feedback(activity_id: int, payload: ActivityFeedbackPayload, user=Depends(current_user)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="O feedback deve ser enviado pelo aluno.")
    integration = repository.get(user.id, "strava")
    if integration is None or not integration.active:
        raise HTTPException(status_code=404, detail="Conta Strava não conectada.")
    activity = activities.get_for_integration(activity_id, integration.id)
    athlete_id = access.athlete_for_student(user.id)
    if activity is None or athlete_id is None:
        raise HTTPException(status_code=404, detail="Atividade ou perfil de atleta não encontrado.")
    return serialize_feedback(feedbacks.save(activity.id, athlete_id, payload))


@router.get("/athletes/{athlete_id}/activities")
def athlete_strava_activities(
    athlete_id: int,
    coach=Depends(require_coach),
):
    require_athlete_access(
        athlete_id,
        coach,
    )

    items = activities.list_for_athlete(
        athlete_id,
    )

    return list(reversed(items))[:50]


@router.get(
    "/athletes/{athlete_id}/activities/{activity_id}/details"
)
def athlete_strava_activity_details(
    athlete_id: int,
    activity_id: int,
    coach=Depends(require_coach),
):
    require_athlete_access(
        athlete_id,
        coach,
    )

    athlete_activities = activities.list_for_athlete(
        athlete_id,
    )

    activity = next(
        (
            item
            for item in athlete_activities
            if item.id == activity_id
        ),
        None,
    )

    if activity is None:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada para este atleta.",
        )

    integration = repository.get_by_id(
        activity.integration_id,
    )

    if integration is None or not integration.active:
        raise HTTPException(
            status_code=404,
            detail="Conta Strava do atleta não está conectada.",
        )

    try:
        integration = refresh_strava_token(
            integration,
        )

        detail = strava_request(
            (
                "https://www.strava.com/api/v3/activities/"
                f"{activity.provider_activity_id}"
            ),
            integration.access_token,
        )

        laps = strava_request(
            (
                "https://www.strava.com/api/v3/activities/"
                f"{activity.provider_activity_id}/laps"
            ),
            integration.access_token,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=(
                "Não foi possível carregar os detalhes "
                "da atividade no Strava."
            ),
        )

    def kilometers(value):
        return round(
            (value or 0) / 1000,
            3,
        )

    activity_feedback = feedbacks.get_for_activity(
        activity.id,
    )

    analysis = ActivityAnalysisService.analyse(
        activity,
        laps,
        activity_feedback,
    )

    return {
        "activity_id": activity.id,
        "name": activity.name,
        "sport_type": activity.sport_type,
        "distance": activity.distance,
        "moving_time": activity.moving_time,
        "start_at": activity.start_at,
        "training_session_id": (
            activity.training_session_id
        ),
        "analysis": analysis,
        "average_heartrate": detail.get(
            "average_heartrate"
        ),
        "max_heartrate": detail.get(
            "max_heartrate"
        ),
        "total_elevation_gain": detail.get(
            "total_elevation_gain"
        ),
        "average_cadence": detail.get(
            "average_cadence"
        ),
        "max_cadence": activity.max_cadence,
        "average_speed": detail.get(
            "average_speed"
        ),
        "max_speed": detail.get(
            "max_speed"
        ),
        "elapsed_time": detail.get(
            "elapsed_time"
        ),
        "laps": [
            {
                "number": index + 1,
                "distance": kilometers(
                    lap.get("distance")
                ),
                "moving_time": lap.get(
                    "moving_time",
                    0,
                ),
                "elapsed_time": lap.get(
                    "elapsed_time",
                    0,
                ),
                "average_speed": lap.get(
                    "average_speed"
                ),
                "max_speed": lap.get(
                    "max_speed"
                ),
                "average_heartrate": lap.get(
                    "average_heartrate"
                ),
                "max_heartrate": lap.get(
                    "max_heartrate"
                ),
                "average_cadence": lap.get(
                    "average_cadence"
                ),
                "elevation_gain": lap.get(
                    "total_elevation_gain"
                ),
            }
            for index, lap in enumerate(laps)
        ],
    }


@router.get("/athletes/{athlete_id}/training-load")
def athlete_training_load(athlete_id: int, coach=Depends(require_coach)):
    # Compatibilidade com atletas criados antes do vínculo treinador-atleta.
    # Se o treinador já consegue abrir o cadastro, ele passa a ter a carga
    # disponível sem precisar recriar ou aprovar o atleta novamente.
    if not access.coach_has_athlete(coach.id, athlete_id):
        access.link_coach_to_athlete(coach.id, athlete_id)

    session = SessionLocal()
    rows = session.execute(
        text("""
        SELECT imported_activities.start_at, imported_activities.moving_time,
               activity_feedbacks.perceived_effort
        FROM activity_feedbacks
        JOIN imported_activities ON imported_activities.id = activity_feedbacks.activity_id
        WHERE activity_feedbacks.athlete_id = :athlete_id
          AND imported_activities.start_at >= :start_at
        ORDER BY imported_activities.start_at ASC
        """),
        {"athlete_id": athlete_id, "start_at": datetime.now() - timedelta(days=42)},
    ).all()
    session.close()

    start = datetime.now().date() - timedelta(days=41)
    daily = {start + timedelta(days=index): 0.0 for index in range(42)}
    for item in rows:
        if item.start_at:
            # Consultas SQL diretas no SQLite devolvem a data como texto,
            # enquanto outros bancos podem devolvê-la como datetime.
            started_at = item.start_at
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            day = started_at.date()
            if day in daily:
                daily[day] += round((item.moving_time or 0) / 60 * item.perceived_effort, 1)

    fitness = fatigue = 0.0
    points = []
    loads = list(daily.values())
    for day, load in daily.items():
        fitness += (load - fitness) / 42
        fatigue += (load - fatigue) / 7
        points.append({"date": day.isoformat(), "load": round(load, 1), "fitness": round(fitness, 1), "fatigue": round(fatigue, 1), "form": round(fitness - fatigue, 1)})

    recent = loads[-7:]
    average = sum(recent) / len(recent) if recent else 0
    deviation = (sum((value - average) ** 2 for value in recent) / len(recent)) ** .5 if recent else 0
    monotony = round(average / deviation, 2) if deviation else 0
    weekly_load = round(sum(recent), 1)
    return {"points": points, "weekly_load": weekly_load, "monotony": monotony, "strain": round(weekly_load * monotony, 1), "feedback_count": len(rows)}


@router.post("/strava/sync")
def sync_strava_activities(user=Depends(current_user)):
    integration = repository.get(user.id, "strava")
    if integration is None or not integration.active:
        raise HTTPException(status_code=404, detail="Conta Strava não conectada.")
    try:
        integration = refresh_strava_token(integration)
        data = strava_request("https://www.strava.com/api/v3/athlete/activities?per_page=20", integration.access_token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Não foi possível sincronizar atividades com o Strava.")

    imported = 0
    for activity in data:
        item = activities.get_by_provider_id(activity["id"])
        if item is None:
            item = ImportedActivity(integration_id=integration.id, provider_activity_id=str(activity["id"]))
            imported += 1
        # Uma mesma conta Strava pode ter sido usada durante testes em outro
        # perfil RunCore. A sincronização atual passa a ser a proprietária dos
        # registros importados, para que eles apareçam para o aluno conectado.
        item.integration_id = integration.id
        item.name = activity.get("name", "Atividade")
        item.sport_type = activity.get("sport_type") or activity.get("type", "")
        item.distance = round(activity.get("distance", 0) / 1000, 3)
        item.moving_time = activity.get("moving_time", 0)
        item.elapsed_time = activity.get("elapsed_time")
        item.average_speed = activity.get("average_speed")
        item.max_speed = activity.get("max_speed")
        item.average_heartrate = activity.get("average_heartrate")
        item.max_heartrate = activity.get("max_heartrate")
        item.average_cadence = activity.get("average_cadence")
        item.total_elevation_gain = activity.get("total_elevation_gain")
        item.start_at = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00")) if activity.get("start_date") else None
        saved_item = activities.save(item)

        sport_type = str(
            activity.get("sport_type")
            or activity.get("type")
            or ""
        ).lower()

        local_start = activity.get(
            "start_date_local",
        )
        local_day = None

        if local_start:
            local_day = datetime.fromisoformat(
                local_start.replace(
                    "Z",
                    "+00:00",
                )
            ).date()

        if sport_type in {
            "run",
            "virtualrun",
            "trailrun",
        }:
            athlete_id = access.athlete_for_student(
                user.id,
            )
            activities.link_training_session(
                saved_item.id,
                athlete_id,
                local_day,
            )

    return {"imported": imported, "activities": activities.list_for_integration(integration.id)}
