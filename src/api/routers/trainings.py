from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status

from api.schemas import TrainingCreate, TrainingOut, TrainingSessionUpdate
from core.training.training_persistence_service import TrainingPersistenceService
from repositories.athlete_repository import AthleteRepository
from repositories.evaluation_repository import EvaluationRepository
from repositories.ipt_repository import IptRepository
from database.database import SessionLocal
from models.athlete import Athlete
from models.goal import Goal
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


def get_latest_evaluation(athlete_id: int):
    evaluation = evaluation_repository.last_evaluation(athlete_id)
    if evaluation is None:
        raise HTTPException(status_code=409, detail="Registre uma avaliação antes de gerar o planejamento.")
    return evaluation


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
                Goal.target_date >= start_date,
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
        "type": step.type,
        "distance": step.distance,
        "distance_unit": step.distance_unit or ("m" if step.repetitions else "km"),
        "repetitions": step.repetitions,
        "recovery": step.recovery,
        "pace_min": step.pace_min,
        "pace_max": step.pace_max,
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
            "type": "Recuperação",
            "distance": distance,
            "distance_unit": unit,
            "repetitions": interval_step["repetitions"],
            "recovery": "",
            "pace_min": "",
            "pace_max": "",
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
    evaluation = get_latest_evaluation(athlete_id)
    goal = get_primary_goal(athlete_id, payload.start_date)
    goal_data = goal_training_data(goal, payload.start_date)

    if goal_data:
        objective = goal_data['objective']
        target_distance = goal_data['target_distance']
        target_date = goal_data['target_date']
        total_weeks = goal_data['total_weeks']
    else:
        weeks_from_date = (
            weeks_between_dates(
                payload.start_date,
                payload.target_date,
            )
            if payload.target_date
            else None
        )
        objective = payload.objective
        target_distance = payload.target_distance
        target_date = payload.target_date
        total_weeks = payload.total_weeks or weeks_from_date or 8

    training = persistence_service.create_training(
        athlete_id=athlete_id,
        vdot=evaluation.vdot,
        name=payload.name,
        methodology="Jack Daniels",
        objective=objective,
        target_distance=target_distance,
        start_date=payload.start_date,
        target_date=target_date,
        total_weeks=total_weeks,
        ipt_profile=get_latest_ipt_profile(athlete_id),
    )
    return serialize_training(training_repository.get_by_id(training.id))


@router.post("/regenerate", response_model=TrainingOut)
def regenerate_training(athlete_id: int):
    get_athlete(athlete_id)
    evaluation = get_latest_evaluation(athlete_id)
    training = training_repository.get_active_by_athlete(athlete_id)
    if training is None:
        raise HTTPException(status_code=404, detail="Não há planejamento ativo para regenerar.")
    cycle_start = training.start_date or date.today()
    goal = get_primary_goal(athlete_id, cycle_start)
    goal_data = goal_training_data(goal, cycle_start)
    total_weeks = None

    if goal_data:
        training.objective = goal_data['objective']
        training.target_distance = goal_data['target_distance']
        training.target_date = goal_data['target_date']
        training_repository.update(training)
        total_weeks = goal_data['total_weeks']

    persistence_service.regenerate_training(
        training.id,
        evaluation.vdot,
        ipt_profile=get_latest_ipt_profile(athlete_id),
        total_weeks=total_weeks,
    )
    return serialize_training(training_repository.get_by_id(training.id))


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

    session.zone = payload.zone
    session.planned_distance = payload.planned_distance
    session.repetitions = payload.repetitions
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
