from fastapi import APIRouter
from fastapi import HTTPException

from core.physiology.vdot_service import VdotService
from repositories.evaluation_repository import EvaluationRepository

from api.schemas import EvaluationCreate
from api.schemas import EvaluationOut

router = APIRouter(tags=["evaluations"])
repository = EvaluationRepository()


@router.get(
    "/athletes/{athlete_id}/evaluations",
    response_model=list[EvaluationOut],
)
def list_evaluations(athlete_id: int):
    return repository.list_by_athlete(athlete_id)


@router.post(
    "/athletes/{athlete_id}/evaluations",
    response_model=EvaluationOut,
    status_code=201,
)
def create_evaluation(athlete_id: int, payload: EvaluationCreate):

    vdot = VdotService.calculate(
        payload.distance,
        payload.time_seconds,
    )

    return repository.create(
        athlete_id=athlete_id,
        weight=payload.weight,
        height=payload.height,
        max_hr=payload.max_hr,
        resting_hr=payload.resting_hr,
        test_type=payload.test_type,
        distance=payload.distance,
        time_seconds=payload.time_seconds,
        vdot=vdot,
    )


@router.put(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationOut,
)
def update_evaluation(evaluation_id: int, payload: EvaluationCreate):

    evaluation = repository.get_by_id(evaluation_id)

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada",
        )

    evaluation.weight = payload.weight
    evaluation.height = payload.height
    evaluation.max_hr = payload.max_hr
    evaluation.resting_hr = payload.resting_hr
    evaluation.test_type = payload.test_type
    evaluation.distance = payload.distance
    evaluation.time_seconds = payload.time_seconds
    evaluation.vdot = VdotService.calculate(
        payload.distance,
        payload.time_seconds,
    )

    return repository.update(evaluation)


@router.delete(
    "/evaluations/{evaluation_id}",
    status_code=204,
)
def delete_evaluation(evaluation_id: int):

    deleted = repository.delete(evaluation_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Avaliação não encontrada",
        )
