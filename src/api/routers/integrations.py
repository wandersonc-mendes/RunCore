import os
import json
import logging
import secrets
import time
from base64 import b64encode
from datetime import datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
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


logger = logging.getLogger(__name__)


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
STRAVA_API_BASE_URL = "https://api-v3.strava.com"
STRAVA_STREAM_KEYS = (
    "time", "distance", "latlng", "altitude",
    "velocity_smooth", "heartrate", "cadence",
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


def strava_webhook_verify_token():
    return os.getenv("STRAVA_WEBHOOK_VERIFY_TOKEN", "")


def process_strava_webhook_event(event):
    if (
        event.get("object_type") != "activity"
        or event.get("aspect_type") not in {"create", "delete"}
    ):
        return

    owner_id = event.get("owner_id")
    object_id = event.get("object_id")
    if not isinstance(owner_id, int) or not isinstance(object_id, int):
        logger.warning("Evento Strava ignorado por IDs inválidos.")
        return

    integration = repository.get_by_external_user_id(
        "strava",
        str(owner_id),
    )
    if integration is None:
        logger.warning("Evento Strava sem integração ativa correspondente.")
        return

    if event.get("aspect_type") == "delete":
        activities.mark_strava_activity_deleted(
            integration.id,
            object_id,
        )
        return

    try:
        integration = refresh_strava_token(integration)
        activity = strava_request(
            strava_api_url(f"activities/{object_id}"),
            integration.access_token,
        )
        athlete_id = access.athlete_for_student(integration.user_id)
        activities.sync_strava_batch(
            integration.id,
            [activity],
            athlete_id=athlete_id,
        )
    except Exception:
        logger.exception(
            "Falha ao processar evento Strava da atividade %s.",
            object_id,
        )


@router.get("/strava/webhook")
def validate_strava_webhook(
    mode: str = Query(alias="hub.mode"),
    challenge: str = Query(alias="hub.challenge"),
    verify_token: str = Query(alias="hub.verify_token"),
):
    expected_token = strava_webhook_verify_token()
    if (
        not expected_token
        or mode != "subscribe"
        or not secrets.compare_digest(verify_token, expected_token)
    ):
        raise HTTPException(
            status_code=403,
            detail="Verificação de webhook inválida.",
        )
    return {"hub.challenge": challenge}


@router.post("/strava/webhook")
def receive_strava_webhook(
    event: dict,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(process_strava_webhook_event, event)
    return {"received": True}


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


def strava_api_url(path):
    return f"{STRAVA_API_BASE_URL}/{path.lstrip('/')}"


def normalize_strava_streams(payload):
    if isinstance(payload, list):
        payload = {
            item.get("type"): item
            for item in payload
            if isinstance(item, dict) and item.get("type")
        }
    if not isinstance(payload, dict):
        return {}

    streams = {}
    for key in STRAVA_STREAM_KEYS:
        stream = payload.get(key)
        if isinstance(stream, dict) and isinstance(stream.get("data"), list):
            streams[key] = stream["data"]
    return streams


def calculate_kilometer_splits(streams):
    distances = streams.get("distance", [])
    times = streams.get("time", [])
    point_count = min(len(distances), len(times))
    if point_count < 2:
        return []

    splits = []
    start_distance = float(distances[0] or 0)
    start_time = float(times[0] or 0)
    target_distance = (int(start_distance // 1000) + 1) * 1000

    for index in range(1, point_count):
        previous_distance = float(distances[index - 1] or 0)
        current_distance = float(distances[index] or 0)
        if current_distance <= previous_distance:
            continue
        previous_time = float(times[index - 1] or 0)
        current_time = float(times[index] or 0)

        while target_distance <= current_distance:
            ratio = (
                (target_distance - previous_distance)
                / (current_distance - previous_distance)
            )
            target_time = previous_time + ratio * (current_time - previous_time)
            duration = max(target_time - start_time, 0)
            distance = target_distance - start_distance
            splits.append({
                "number": len(splits) + 1,
                "distance": round(distance / 1000, 3),
                "moving_time": round(duration),
                "average_speed": distance / duration if duration > 0 else None,
            })
            start_distance = target_distance
            start_time = target_time
            target_distance += 1000

    final_distance = float(distances[point_count - 1] or 0)
    final_time = float(times[point_count - 1] or 0)
    remaining_distance = final_distance - start_distance
    remaining_time = final_time - start_time
    if remaining_distance >= 100 and remaining_time > 0:
        splits.append({
            "number": len(splits) + 1,
            "distance": round(remaining_distance / 1000, 3),
            "moving_time": round(remaining_time),
            "average_speed": remaining_distance / remaining_time,
        })
    return splits


def serialize_activity_streams(streams):
    point_count = max((len(values) for values in streams.values()), default=0)
    points = []
    for index in range(point_count):
        point = {}
        for key in STRAVA_STREAM_KEYS:
            values = streams.get(key, [])
            if index < len(values):
                point[key] = values[index]
        points.append(point)

    pace_is_derived = False
    if (
        not streams.get("velocity_smooth")
        and streams.get("time")
        and streams.get("distance")
    ):
        pace_is_derived = True
        for index in range(1, len(points)):
            elapsed = float(points[index].get("time") or 0) - float(
                points[index - 1].get("time") or 0
            )
            distance = float(points[index].get("distance") or 0) - float(
                points[index - 1].get("distance") or 0
            )
            if elapsed > 0 and distance >= 0:
                points[index]["velocity_smooth"] = distance / elapsed

    return {
        "points": points,
        "available": {
            key: bool(streams.get(key)) or (
                key == "velocity_smooth" and pace_is_derived
            )
            for key in STRAVA_STREAM_KEYS
        },
        "pace_is_derived": pace_is_derived,
        "splits": calculate_kilometer_splits(streams),
        "physiology_ready": bool(
            streams.get("time")
            and streams.get("distance")
            and streams.get("heartrate")
        ),
    }


def load_strava_activity_data(integration, activity):
    integration = refresh_strava_token(integration)
    provider_activity_id = activity.provider_activity_id
    detail = strava_request(
        strava_api_url(f"activities/{provider_activity_id}"),
        integration.access_token,
    )
    laps = strava_request(
        strava_api_url(f"activities/{provider_activity_id}/laps"),
        integration.access_token,
    )
    query = urlencode({
        "keys": ",".join(STRAVA_STREAM_KEYS),
        "key_by_type": "true",
    })
    try:
        stream_payload = strava_request(
            strava_api_url(f"activities/{provider_activity_id}/streams?{query}"),
            integration.access_token,
        )
    except HTTPException:
        logger.warning(
            "Streams indisponíveis para a atividade Strava %s.",
            provider_activity_id,
        )
        stream_payload = {}
    return detail, laps, normalize_strava_streams(stream_payload)


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

    integration.external_user_id = str(result["athlete"]["id"])
    integration.access_token = result["access_token"]
    integration.refresh_token = result["refresh_token"]
    integration.expires_at = result["expires_at"]
    integration.scopes = scope
    integration.active = True
    repository.save(integration)

    return RedirectResponse(f"{frontend_url}/?strava=connected")


@router.delete("/strava/disconnect")
def disconnect_strava(user=Depends(current_user)):
    integration = repository.get(
        user.id,
        "strava",
    )

    if integration is None or not integration.active:
        return {
            "connected": False,
            "message": "Conta Strava já está desconectada.",
        }

    token = (
        integration.refresh_token
        or integration.access_token
    )

    if token:
        credentials = (
            f"{os.environ['STRAVA_CLIENT_ID']}:"
            f"{os.environ['STRAVA_CLIENT_SECRET']}"
        )

        authorization = b64encode(
            credentials.encode(),
        ).decode()

        form = urlencode({
            "token": token,
            "token_type_hint": (
                "refresh_token"
                if integration.refresh_token
                else "access_token"
            ),
        }).encode()

        request = Request(
            "https://www.strava.com/oauth/revoke",
            data=form,
            method="POST",
            headers={
                "Authorization": (
                    f"Basic {authorization}"
                ),
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
            },
        )

        try:
            with urlopen(
                request,
                timeout=15,
            ) as response:
                if response.status != 200:
                    raise RuntimeError(
                        "Falha ao revogar autorização."
                    )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Não foi possível desvincular a conta "
                    "no Strava. Tente novamente."
                ),
            ) from exc

    integration.active = False
    integration.access_token = ""
    integration.refresh_token = ""
    integration.expires_at = 0
    integration.scopes = ""

    repository.save(integration)

    return {
        "connected": False,
        "message": (
            "Conta Strava desvinculada com sucesso. "
            "As atividades já importadas foram preservadas."
        ),
    }


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
        detail, laps, streams = load_strava_activity_data(integration, activity)
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
        "strava_profile_url": f"https://www.strava.com/athletes/{integration.external_user_id}",
        "strava_activity_url": f"https://www.strava.com/activities/{activity.provider_activity_id}",
        "streams": serialize_activity_streams(streams),
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


@router.post("/athletes/{athlete_id}/strava/sync")
def sync_athlete_strava_activities(
    athlete_id: int,
    coach=Depends(require_coach),
):
    athlete = require_athlete_access(
        athlete_id,
        coach,
    )

    if athlete.user_id is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Este atleta ainda não possui um usuário "
                "vinculado no RunCore."
            ),
        )

    integration = repository.get(
        athlete.user_id,
        "strava",
    )

    if integration is None:
        raise HTTPException(
            status_code=404,
            detail="Este atleta não possui uma conta Strava conectada.",
        )

    if not integration.active:
        raise HTTPException(
            status_code=409,
            detail=(
                "A integração Strava deste atleta está inativa. "
                "Peça ao atleta para reconectar a conta."
            ),
        )

    try:
        integration = refresh_strava_token(
            integration,
        )
        data = strava_request(
            (
                f"{STRAVA_API_BASE_URL}/athlete/"
                "activities?per_page=20"
            ),
            integration.access_token,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Falha na sincronização manual do Strava para o atleta %s.",
            athlete_id,
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "Não foi possível sincronizar as atividades deste "
                "atleta com o Strava."
            ),
        )

    provider_ids = {
        str(item["id"])
        for item in data
        if item.get("id") is not None
    }
    imported = activities.sync_strava_batch(
        integration.id,
        data,
        athlete_id=athlete_id,
    )

    return {
        "imported": imported,
        "updated": max(len(provider_ids) - imported, 0),
    }


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
        detail, laps, streams = load_strava_activity_data(integration, activity)
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
        "strava_profile_url": (
            "https://www.strava.com/athletes/"
            f"{integration.external_user_id}"
        ),
        "strava_activity_url": (
            "https://www.strava.com/activities/"
            f"{activity.provider_activity_id}"
        ),
        "streams": serialize_activity_streams(streams),
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
    require_athlete_access(
        athlete_id,
        coach,
    )

    session = SessionLocal()
    rows = session.execute(
        text("""
        SELECT imported_activities.start_at, imported_activities.moving_time,
               activity_feedbacks.perceived_effort
        FROM activity_feedbacks
        JOIN imported_activities ON imported_activities.id = activity_feedbacks.activity_id
        WHERE activity_feedbacks.athlete_id = :athlete_id
          AND imported_activities.deleted_at IS NULL
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
        data = strava_request(
            strava_api_url("athlete/activities?per_page=20"),
            integration.access_token,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Não foi possível sincronizar atividades com o Strava.")

    athlete_id = access.athlete_for_student(
        user.id,
    )

    imported = activities.sync_strava_batch(
        integration.id,
        data,
        athlete_id=athlete_id,
    )
    removed = activities.mark_recent_missing_strava_activities(
        integration.id,
        data,
    )

    return {
        "imported": imported,
        "removed": removed,
        "activities": activities.list_for_integration(
            integration.id,
        ),
    }
