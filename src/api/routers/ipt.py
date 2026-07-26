from fastapi import APIRouter
from fastapi import HTTPException

from api.schemas import IptAssessmentCreate
from api.schemas import IptAssessmentOut
from api.schemas import IptProtocolOut
from core.physiology.ipt_service import IptService
from repositories.athlete_repository import AthleteRepository
from repositories.ipt_repository import IptRepository


router = APIRouter(tags=["ipt"])
repository = IptRepository()
athlete_repository = AthleteRepository()


@router.get(
    "/ipt/protocols",
    response_model=list[IptProtocolOut],
)
def list_protocols():

    repository.ensure_default_protocols()

    return repository.list_protocols()


@router.get(
    "/athletes/{athlete_id}/ipt-assessments",
    response_model=list[IptAssessmentOut],
)
def list_assessments(athlete_id: int):

    if athlete_repository.get_by_id(athlete_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta nÃ£o encontrado",
        )

    return repository.list_by_athlete(athlete_id)


@router.post(
    "/athletes/{athlete_id}/ipt-assessments",
    response_model=IptAssessmentOut,
    status_code=201,
)
def create_assessment(
    athlete_id: int,
    payload: IptAssessmentCreate,
):

    if athlete_repository.get_by_id(athlete_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta nÃ£o encontrado",
        )

    repository.ensure_default_protocols()

    protocol = repository.get_protocol(payload.protocol_id)

    if protocol is None or not protocol.active:
        raise HTTPException(
            status_code=404,
            detail="Protocolo IPT nÃ£o encontrado",
        )

    try:
        result = IptService.calculate(
            protocol_type=protocol.protocol_type,
            short_value=protocol.short_value,
            long_value=protocol.long_value,
            short_result=payload.short_result,
            long_result=payload.long_result,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return repository.create_assessment(
        athlete_id=athlete_id,
        protocol_id=protocol.id,
        short_result=payload.short_result,
        long_result=payload.long_result,
        result=result,
        notes=payload.notes,
    )


@router.delete(
    "/ipt-assessments/{assessment_id}",
    status_code=204,
)
def delete_assessment(assessment_id: int):

    if not repository.delete(assessment_id):
        raise HTTPException(
            status_code=404,
            detail="AvaliaÃ§Ã£o IPT nÃ£o encontrada",
        )