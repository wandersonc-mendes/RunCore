from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from api.analytics_schemas import AthleteAnalyticsResponse
from api.dependencies import require_coach
from repositories.access_repository import AccessRepository
from repositories.athlete_repository import AthleteRepository
from services.athlete_analytics_service import AthleteAnalyticsService

from api.schemas import AthleteCreate
from api.schemas import AthleteOut
from api.schemas import AthleteUpdate

router = APIRouter(prefix="/athletes", tags=["athletes"])
repository = AthleteRepository()
access = AccessRepository()
analytics = AthleteAnalyticsService()


@router.get("", response_model=list[AthleteOut])
def list_athletes(search: str | None = None):

    if search:
        return repository.search(search)

    return repository.list_all()


@router.get(
    "/{athlete_id}/analytics",
    response_model=AthleteAnalyticsResponse,
)
def get_athlete_analytics(
    athlete_id: int,
    coach=Depends(require_coach),
):
    athlete = repository.get_by_id(
        athlete_id,
    )

    if athlete is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )

    if (
        coach.role != "master"
        and not access.coach_has_athlete(
            coach.id,
            athlete_id,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "O atleta não pertence ao treinador autenticado."
            ),
        )

    return analytics.build_for_athlete(
        athlete_id,
    )


@router.get("/{athlete_id}", response_model=AthleteOut)
def get_athlete(athlete_id: int):

    athlete = repository.get_by_id(athlete_id)

    if athlete is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )

    return athlete


@router.post("", response_model=AthleteOut, status_code=201)
def create_athlete(payload: AthleteCreate):

    return repository.create(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        goal=payload.goal,
        active=payload.active,
        notes=payload.notes,
    )


@router.put("/{athlete_id}", response_model=AthleteOut)
def update_athlete(athlete_id: int, payload: AthleteUpdate):

    updated = repository.update(
        athlete_id=athlete_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        goal=payload.goal,
        active=payload.active,
        notes=payload.notes,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )

    return repository.get_by_id(athlete_id)


@router.delete("/{athlete_id}", status_code=204)
def delete_athlete(athlete_id: int):

    deleted = repository.delete(athlete_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )
