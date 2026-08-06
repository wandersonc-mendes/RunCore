from datetime import date, timedelta
from math import exp

from fastapi import APIRouter, HTTPException, Query, status

from api.schemas import (
    TrainingCreate,
    TrainingOut,
    TrainingSessionCreate,
    TrainingSessionOut,
    TrainingSessionUpdate,
)
from core.training.training_persistence_service import TrainingPersistenceService
from repositories.athlete_repository import AthleteRepository
from repositories.evaluation_repository import EvaluationRepository
from repositories.ipt_repository import IptRepository
from database.database import SessionLocal
from models.athlete import Athlete
from models.goal import Goal
from models.training_session import TrainingSession
from repositories.training_repository import TrainingRepository
from repositories.training_session_repository import TrainingSessionRepository
from repositories.training_step_repository import TrainingStepRepository
from core.training.training_step_service import TrainingStepService


router = APIRouter(prefix="/athletes/{athlete_id}/training", tags=["training"])
athlete_repository = AthleteRepository()
evaluation_repository = EvaluationRepository()
ipt_repository = IptRepository()
training_repository = TrainingRepository()
session_repository = TrainingSessionRepository()
step_repository = TrainingStepRepository()
persistence_service = TrainingPersistenceService()
step_service = TrainingStepService()


def get_athlete(athlete_id: int):
    athlete = athlete_repository.get_by_id(athlete_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    return athlete


def get_optional_evaluation(athlete_id: int):
    return evaluation_repository.last_evaluation(
        athlete_id,
    )


def get_latest_ipt(athlete_id: int):
    return ipt_repository.get_latest_by_athlete(
        athlete_id,
    )


def vdot_from_ipt(assessment) -> float | None:
    if assessment is None:
        return None

    protocol_code = str(
        assessment.get("protocol_code") or ""
    )
    long_result = float(
        assessment.get("long_result") or 0
    )

    distance_protocols = {
        "DIST_500_1600": 1600,
        "DIST_1000_2400": 2400,
        "DIST_1000_3000": 3000,
        "DIST_1000_3200": 3200,
        "DIST_1000_5000": 5000,
    }

    time_protocols = {
        "TIME_2_5": 300,
        "TIME_4_12": 720,
    }

    if (
        protocol_code in distance_protocols
        and long_result > 0
    ):
        distance_m = distance_protocols[
            protocol_code
        ]
        duration_seconds = long_result
    elif (
        protocol_code in time_protocols
        and long_result > 0
    ):
        distance_m = long_result
        duration_seconds = time_protocols[
            protocol_code
        ]
    else:
        return None

    duration_minutes = duration_seconds / 60

    if duration_minutes <= 0:
        return None

    velocity_m_min = distance_m / duration_minutes

    oxygen_cost = (
        -4.60
        + 0.182258 * velocity_m_min
        + 0.000104 * velocity_m_min ** 2
    )

    fraction = (
        0.8
        + 0.1894393
        * exp(-0.012778 * duration_minutes)
        + 0.2989558
        * exp(-0.1932605 * duration_minutes)
    )

    if fraction <= 0:
        return None

    return round(oxygen_cost / fraction, 2)


def training_reference(athlete_id: int):
    evaluation = get_optional_evaluation(
        athlete_id,
    )
    ipt_assessment = get_latest_ipt(
        athlete_id,
    )

    vdot = (
        float(evaluation.vdot)
        if evaluation is not None
        else vdot_from_ipt(ipt_assessment)
    )

    methodology = (
        "Jack Daniels"
        if evaluation is not None
        else (
            "IPT/Avaliação"
            if ipt_assessment is not None
            else "Observação inicial"
        )
    )

    return {
        "evaluation": evaluation,
        "ipt": ipt_assessment,
        "vdot": vdot,
        "methodology": methodology,
        "ipt_profile": (
            ipt_assessment.get("profile")
            if ipt_assessment
            else None
        ),
    }


def get_latest_ipt_profile(athlete_id: int) -> str | None:
    assessment = ipt_repository.get_latest_by_athlete(athlete_id)

    if assessment is None:
        return None

    return assessment["profile"]


def weeks_between_dates(start_date, target_date) -> int:
    days = (target_date - start_date).days

    if days <= 0:
        raise ValueError(
            'A data da meta precisa ser posterior ao início do ciclo.'
        )

    return max(4, (days // 7) + 1)


def get_primary_goal(athlete_id: int, start_date):
    session = SessionLocal()

    try:
        athlete = session.get(Athlete, athlete_id)

        if athlete is None or athlete.user_id is None:
            return None

        goals = (
            session.query(Goal)
            .filter(
                Goal.user_id == athlete.user_id,
                Goal.target_date > start_date,
                Goal.status == 'Em andamento',
            )
            .order_by(Goal.target_date.asc())
            .all()
        )

        principal = next(
            (
                goal
                for goal in goals
                if str(goal.priority).strip().lower() == 'principal'
            ),
            None,
        )

        return principal or (goals[0] if goals else None)
    finally:
        session.close()


def get_goal_for_training(
    athlete_id: int,
    goal_id: int,
    start_date,
):
    session = SessionLocal()

    try:
        athlete = session.get(
            Athlete,
            athlete_id,
        )

        if athlete is None or athlete.user_id is None:
            return None

        goal = (
            session.query(Goal)
            .filter(
                Goal.id == goal_id,
                Goal.user_id == athlete.user_id,
                Goal.target_date > start_date,
                Goal.status == "Em andamento",
            )
            .first()
        )

        if goal is not None:
            session.expunge(goal)

        return goal
    finally:
        session.close()


def goal_training_data(goal, start_date):
    if goal is None:
        return None

    return {
        'objective': goal.name,
        'target_distance': float(goal.distance),
        'target_date': goal.target_date,
        'total_weeks': weeks_between_dates(
            start_date,
            goal.target_date,
        ),
    }


def phase_for_week(week: int, total_weeks: int) -> str:
    if week == total_weeks:
        return "Competição"

    ratio = week / max(total_weeks, 1)
    if ratio <= .40:
        return "Base"
    if ratio <= .75:
        return "Desenvolvimento"
    if ratio <= .90:
        return "Específica"
    return "Polimento"


def adaptations_for(zone: str) -> list[str]:
    key = zone.lower()
    if "interval" in key or "repetition" in key:
        return ["Melhora o consumo máximo de oxigênio", "Aumenta a economia de corrida em ritmos altos", "Desenvolve potência e coordenação neuromuscular"]
    if "threshold" in key or "limiar" in key:
        return ["Eleva o limiar de lactato", "Melhora a capacidade de sustentar ritmo forte", "Aprimora a resistência muscular"]
    if "marathon" in key or "long" in key or "longão" in key:
        return ["Aumenta a resistência aeróbica", "Melhora o uso de gordura como combustível", "Fortalece músculos e tendões para esforços prolongados"]
    return ["Constrói base aeróbica", "Favorece recuperação entre treinos intensos", "Melhora a eficiência cardiovascular"]


def serialize_step(step):
    return {
        "id": step.id,
        "order": step.order,
        "group_id": step.group_id,
        "group_order": step.group_order,
        "group_repetitions": (
            step.group_repetitions or 1
        ),
        "type": step.type,
        "prescription_type": (
            step.prescription_type
            or "distance"
        ),
        "intensity_type": (
            step.intensity_type
            or "pace"
        ),
        "distance": step.distance,
        "distance_unit": (
            step.distance_unit
            or ("m" if step.repetitions else "km")
        ),
        "duration": step.duration,
        "repetitions": step.repetitions,
        "recovery": step.recovery,
        "pace_min": step.pace_min,
        "pace_max": step.pace_max,
        "heart_rate_min": step.heart_rate_min,
        "heart_rate_max": step.heart_rate_max,
        "rpe_min": step.rpe_min,
        "rpe_max": step.rpe_max,
        "notes": step.notes,
    }


def serialized_steps_for_session(
    session,
    steps_by_session=None,
):
    if steps_by_session is None:
        source_steps = step_repository.list_by_session(
            session.id
        )
    else:
        source_steps = steps_by_session.get(
            session.id,
            [],
        )

    steps = [
        serialize_step(step)
        for step in source_steps
    ]
    has_recovery_step = any("recupera" in item["type"].lower() or "descanso" in item["type"].lower() for item in steps)
    interval_step = next((item for item in steps if item["repetitions"] and item.get("recovery")), None)
    if interval_step and not has_recovery_step:
        import re
        found = re.search(r"(\d+(?:[.,]\d+)?)\s*(km|m)", interval_step["recovery"].lower())
        distance = float(found.group(1).replace(",", ".")) if found else 0
        unit = found.group(2) if found else "m"
        position = steps.index(interval_step) + 1
        steps.insert(position, {
            "id": None,
            "order": interval_step["order"],
            "group_id": interval_step.get("group_id"),
            "group_order": interval_step.get("group_order"),
            "group_repetitions": interval_step.get(
                "group_repetitions",
                1,
            ),
            "type": "Recuperação",
            "prescription_type": "distance",
            "intensity_type": "free",
            "distance": distance,
            "distance_unit": unit,
            "duration": 0,
            "repetitions": interval_step["repetitions"],
            "recovery": "",
            "pace_min": "",
            "pace_max": "",
            "heart_rate_min": None,
            "heart_rate_max": None,
            "rpe_min": None,
            "rpe_max": None,
            "notes": interval_step["recovery"],
        })
    for order, item in enumerate(steps, start=1):
        item["order"] = order
    return steps


def serialize_training(training):
    sessions = session_repository.list_by_training(training.id)
    steps_by_session = step_repository.list_by_sessions(
        [session.id for session in sessions]
    )
    total_weeks = max((item.week for item in sessions), default=1)
    current_week = 1
    if training.start_date:
        current_week = max(1, ((date.today() - training.start_date).days // 7) + 1)
    current_week = min(current_week, total_weeks)
    return {
        "id": training.id,
        "athlete_id": training.athlete_id,
        "name": training.name,
        "methodology": training.methodology,
        "objective": training.objective,
        "target_distance": training.target_distance,
        "start_date": training.start_date,
        "target_date": training.target_date,
        "total_weeks": total_weeks,
        "current_week": current_week,
        "current_phase": phase_for_week(current_week, total_weeks),
        "active": training.active,
        "sessions": [
            {
                "id": session.id,
                "week": session.week,
                "weekday": session.weekday,
                "workout_name": session.workout_name,
                "zone": session.zone,
                "planned_distance": session.planned_distance,
                "repetitions": session.repetitions,
                "recovery": session.recovery,
                "objective": session.objective or "",
                "notes": session.notes or "",
                "completed": session.completed,
                "session_date": session.scheduled_date or ((training.start_date + timedelta(days=((session.week - 1) * 7) + session.weekday)) if training.start_date else None),
                "phase": phase_for_week(session.week, total_weeks),
                "adaptations": adaptations_for(session.zone),
                "steps": serialized_steps_for_session(session, steps_by_session),
            }
            for session in sessions
        ],
    }


@router.get("", response_model=TrainingOut | None)
def get_active_training(athlete_id: int):
    get_athlete(athlete_id)
    training = training_repository.get_active_by_athlete(athlete_id)
    return serialize_training(training) if training else None


@router.post("", response_model=TrainingOut, status_code=status.HTTP_201_CREATED)
def create_training(athlete_id: int, payload: TrainingCreate):
    get_athlete(athlete_id)
    if training_repository.get_active_by_athlete(athlete_id) is not None:
        raise HTTPException(status_code=409, detail="Este atleta já possui um planejamento ativo.")
    if payload.target_date and payload.target_date <= payload.start_date:
        raise HTTPException(status_code=422, detail="A data da prova precisa ser posterior ao início do ciclo.")
    reference = training_reference(
        athlete_id,
    )

    goal = get_primary_goal(
        athlete_id,
        payload.start_date,
    )

    if goal is not None:
        goal_data = goal_training_data(
            goal,
            payload.start_date,
        )

        objective = goal_data["objective"]
        target_distance = goal_data["target_distance"]
        target_date = goal_data["target_date"]
        total_weeks = goal_data["total_weeks"]
    else:
        objective = payload.objective
        target_distance = payload.target_distance
        target_date = payload.target_date
        total_weeks = payload.total_weeks or 8

    training = persistence_service.create_training(
        athlete_id=athlete_id,
        vdot=reference["vdot"],
        name=payload.name,
        methodology=reference["methodology"],
        objective=objective,
        target_distance=target_distance,
        start_date=payload.start_date,
        target_date=target_date,
        total_weeks=total_weeks,
        ipt_profile=reference["ipt_profile"],
    )
    return serialize_training(training_repository.get_by_id(training.id))


@router.post("/regenerate", response_model=TrainingOut)
def regenerate_training(
    athlete_id: int,
    goal_id: int | None = Query(default=None),
):
    get_athlete(athlete_id)
    reference = training_reference(
        athlete_id,
    )
    training = training_repository.get_active_by_athlete(athlete_id)
    if training is None:
        raise HTTPException(status_code=404, detail="Não há planejamento ativo para regenerar.")
    cycle_start = training.start_date or date.today()
    goal = (
        get_goal_for_training(
            athlete_id,
            goal_id,
            cycle_start,
        )
        if goal_id is not None
        else get_primary_goal(
            athlete_id,
            cycle_start,
        )
    )

    if goal_id is not None and goal is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "A meta selecionada não pertence ao atleta, "
                "não está ativa ou sua data não é posterior "
                "ao início do planejamento."
            ),
        )

    total_weeks = None

    if goal is not None:
        goal_data = goal_training_data(
            goal,
            cycle_start,
        )

        training.objective = goal_data["objective"]
        training.target_distance = goal_data[
            "target_distance"
        ]
        training.target_date = goal_data[
            "target_date"
        ]
        total_weeks = goal_data["total_weeks"]

    training.methodology = reference[
        "methodology"
    ]

    training_repository.update(
        training,
    )

    if reference["vdot"] is not None:
        persistence_service.regenerate_training(
            training.id,
            reference["vdot"],
            ipt_profile=reference[
                "ipt_profile"
            ],
            total_weeks=total_weeks,
        )
    return serialize_training(training_repository.get_by_id(training.id))


@router.post(
    "/sessions",
    response_model=TrainingSessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    athlete_id: int,
    payload: TrainingSessionCreate,
):
    training = training_repository.get_active_by_athlete(
        athlete_id
    )

    if training is None:
        raise HTTPException(
            status_code=404,
            detail="O atleta não possui planejamento ativo.",
        )

    if training.start_date:
        day_offset = (
            payload.session_date - training.start_date
        ).days
        week = max(1, (day_offset // 7) + 1)
    else:
        week = 1

    session = TrainingSession()
    session.training_id = training.id
    session.week = week
    session.weekday = payload.session_date.weekday()
    session.workout_name = payload.workout_name
    session.zone = payload.zone
    session.planned_distance = payload.planned_distance
    session.completed_distance = 0
    session.planned_duration = 0
    session.completed_duration = 0
    session.repetitions = payload.repetitions
    session.recovery = 0
    session.rpe = 0
    session.objective = payload.objective
    session.notes = payload.notes
    session.completed = False
    session.scheduled_date = payload.session_date

    created = session_repository.create(session)

    step_service.save(
        created.id,
        [
            step.model_dump()
            for step in payload.steps
        ],
    )

    refreshed = session_repository.get_by_id(created.id)
    total_weeks = max(
        (
            item.week
            for item in session_repository.list_by_training(
                training.id
            )
        ),
        default=1,
    )

    return {
        "id": refreshed.id,
        "week": refreshed.week,
        "weekday": refreshed.weekday,
        "workout_name": refreshed.workout_name,
        "zone": refreshed.zone,
        "planned_distance": refreshed.planned_distance,
        "repetitions": refreshed.repetitions,
        "recovery": refreshed.recovery,
        "objective": refreshed.objective or "",
        "notes": refreshed.notes or "",
        "completed": refreshed.completed,
        "session_date": refreshed.scheduled_date,
        "phase": phase_for_week(
            refreshed.week,
            total_weeks,
        ),
        "adaptations": adaptations_for(
            refreshed.zone
        ),
        "steps": serialized_steps_for_session(
            refreshed
        ),
    }


@router.patch(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
)
def update_session(
    athlete_id: int,
    session_id: int,
    payload: TrainingSessionUpdate,
):
    training = training_repository.get_active_by_athlete(
        athlete_id
    )
    session = session_repository.get_by_id(
        session_id
    )

    if (
        training is None
        or session is None
        or session.training_id != training.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Sessão de treino não encontrada.",
        )

    session.workout_name = payload.workout_name

    if payload.session_date:
        session.scheduled_date = payload.session_date
        session.weekday = payload.session_date.weekday()

        if training.start_date:
            day_offset = (
                payload.session_date
                - training.start_date
            ).days
            session.week = max(
                1,
                (day_offset // 7) + 1,
            )

    session.zone = payload.zone
    session.planned_distance = payload.planned_distance
    session.repetitions = payload.repetitions
    session.objective = payload.objective
    session.notes = payload.notes

    session_repository.update(
        session
    )

    step_service.save(
        session.id,
        [
            step.model_dump()
            for step in payload.steps
        ],
    )

    return {
        "message": "Treino salvo com sucesso.",
        "session_id": session.id,
    }
