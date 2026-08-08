from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from api.access_control import require_athlete_access
from api.dependencies import current_user
from api.dependencies import require_coach
from core.physiology.vdot_service import VdotService
from repositories.access_repository import AccessRepository
from repositories.evaluation_repository import EvaluationRepository

from api.schemas import EvaluationCreate
from api.schemas import EvaluationOut


router = APIRouter(tags=["evaluations"])
repository = EvaluationRepository()
access = AccessRepository()


TEST_DISTANCES_METERS = {
    "3 km": 3000.0,
    "5 km": 5000.0,
    "10 km": 10000.0,
    "Meia maratona": 21097.5,
    "Maratona": 42195.0,
}


def parse_time_to_seconds(value: str) -> float:
    try:
        parts = value.split(":")

        if len(parts) != 3:
            raise ValueError

        hours, minutes, seconds = map(int, parts)

        if hours < 0:
            raise ValueError

        if minutes < 0 or minutes >= 60:
            raise ValueError

        if seconds < 0 or seconds >= 60:
            raise ValueError

        total_seconds = (
            hours * 3600
            + minutes * 60
            + seconds
        )

        if total_seconds <= 0:
            raise ValueError

        return float(total_seconds)

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Tempo inválido. Use o formato HH:MM:SS.",
        ) from exc


def distance_from_test_type(test_type: str) -> float:
    distance = TEST_DISTANCES_METERS.get(test_type)

    if distance is None:
        raise HTTPException(
            status_code=422,
            detail="Tipo de teste inválido.",
        )

    return distance


@router.get(
    "/student/evaluations",
    response_model=list[EvaluationOut],
)
def list_student_evaluations(
    user=Depends(current_user),
):
    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Avaliações disponíveis apenas para aluno.",
        )

    athlete_id = access.athlete_for_student(user.id)

    if athlete_id is None:
        raise HTTPException(
            status_code=404,
            detail="Perfil de atleta não encontrado.",
        )

    return repository.list_by_athlete(athlete_id)


@router.get(
    "/athletes/{athlete_id}/evaluations",
    response_model=list[EvaluationOut],
)
def list_evaluations(
    athlete_id: int,
    coach=Depends(require_coach),
):
    require_athlete_access(
        athlete_id,
        coach,
    )

    return repository.list_by_athlete(
        athlete_id,
    )


@router.post(
    "/athletes/{athlete_id}/evaluations",
    response_model=EvaluationOut,
    status_code=201,
)
def create_evaluation(
    athlete_id: int,
    payload: EvaluationCreate,
    coach=Depends(require_coach),
):
    require_athlete_access(
        athlete_id,
        coach,
    )

    distance = distance_from_test_type(
        payload.test_type,
    )

    time_seconds = parse_time_to_seconds(
        payload.time,
    )

    vdot = VdotService.calculate(
        distance,
        time_seconds,
    )

    return repository.create(
        athlete_id=athlete_id,
        weight=payload.weight,
        height=payload.height,
        max_hr=payload.max_hr,
        resting_hr=payload.resting_hr,
        test_type=payload.test_type,
        distance=distance,
        time_seconds=time_seconds,
        vdot=vdot,
        test_date=payload.test_date,
    )


@router.put(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationOut,
)
def update_evaluation(
    evaluation_id: int,
    payload: EvaluationCreate,
    coach=Depends(require_coach),
):
    evaluation = repository.get_by_id(
        evaluation_id,
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada.",
        )

    require_athlete_access(
        evaluation.athlete_id,
        coach,
    )

    distance = distance_from_test_type(
        payload.test_type,
    )

    time_seconds = parse_time_to_seconds(
        payload.time,
    )

    vdot = VdotService.calculate(
        distance,
        time_seconds,
    )

    evaluation.weight = payload.weight
    evaluation.height = payload.height
    evaluation.max_hr = payload.max_hr
    evaluation.resting_hr = payload.resting_hr
    evaluation.test_type = payload.test_type
    evaluation.distance = distance
    evaluation.time_seconds = time_seconds
    evaluation.vdot = vdot
    evaluation.test_date = payload.test_date

    return repository.update(
        evaluation,
    )


@router.delete(
    "/evaluations/{evaluation_id}",
    status_code=204,
)
def delete_evaluation(
    evaluation_id: int,
    coach=Depends(require_coach),
):
    evaluation = repository.get_by_id(
        evaluation_id,
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada.",
        )

    require_athlete_access(
        evaluation.athlete_id,
        coach,
    )

    deleted = repository.delete(
        evaluation_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada.",
        )