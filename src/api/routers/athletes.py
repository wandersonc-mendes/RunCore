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


router = APIRouter(
    prefix="/athletes",
    tags=["athletes"],
)

repository = AthleteRepository()
access = AccessRepository()
analytics = AthleteAnalyticsService()


def _coach_can_access_athlete(
    coach,
    athlete,
) -> bool:
    if coach.role == "master":
        return True

    if getattr(
        athlete,
        "coach_user_id",
        None,
    ) == coach.id:
        return True

    return access.coach_has_athlete(
        coach.id,
        athlete.id,
    )


def _require_athlete_access(
    athlete_id: int,
    coach,
):
    athlete = repository.get_by_id(
        athlete_id,
    )

    if athlete is None:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )

    if not _coach_can_access_athlete(
        coach,
        athlete,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "O atleta não pertence ao "
                "treinador autenticado."
            ),
        )

    return athlete


def _visible_athletes(
    coach,
) -> list:
    if coach.role == "master":
        return repository.list_all()

    direct = repository.list_by_coach(
        coach.id,
    )
    linked = access.athletes_for_coach(
        coach.id,
    )

    result = {}
    for athlete in [
        *direct,
        *linked,
    ]:
        result[athlete.id] = athlete

    return sorted(
        result.values(),
        key=lambda athlete: str(
            athlete.name or "",
        ).casefold(),
    )


@router.get(
    "",
    response_model=list[AthleteOut],
)
def list_athletes(
    search: str | None = None,
    coach=Depends(require_coach),
):
    visible = _visible_athletes(
        coach,
    )

    if not search:
        return visible

    normalized = search.strip().casefold()

    if not normalized:
        return visible

    return [
        athlete
        for athlete in visible
        if normalized in str(
            athlete.name or "",
        ).casefold()
    ]


@router.get(
    "/{athlete_id}/analytics",
    response_model=AthleteAnalyticsResponse,
)
def get_athlete_analytics(
    athlete_id: int,
    coach=Depends(require_coach),
):
    _require_athlete_access(
        athlete_id,
        coach,
    )

    return analytics.build_for_athlete(
        athlete_id,
    )


@router.get(
    "/{athlete_id}",
    response_model=AthleteOut,
)
def get_athlete(
    athlete_id: int,
    coach=Depends(require_coach),
):
    return _require_athlete_access(
        athlete_id,
        coach,
    )


@router.post(
    "",
    response_model=AthleteOut,
    status_code=201,
)
def create_athlete(
    payload: AthleteCreate,
    coach=Depends(require_coach),
):
    athlete = repository.create(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        goal=payload.goal,
        active=payload.active,
        notes=payload.notes,
        coach_user_id=(
            None
            if coach.role == "master"
            else coach.id
        ),
    )

    if coach.role != "master":
        access.link_coach_to_athlete(
            coach.id,
            athlete.id,
        )

    return athlete


@router.put(
    "/{athlete_id}",
    response_model=AthleteOut,
)
def update_athlete(
    athlete_id: int,
    payload: AthleteUpdate,
    coach=Depends(require_coach),
):
    _require_athlete_access(
        athlete_id,
        coach,
    )

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

    return repository.get_by_id(
        athlete_id,
    )


@router.delete(
    "/{athlete_id}",
    status_code=204,
)
def delete_athlete(
    athlete_id: int,
    coach=Depends(require_coach),
):
    _require_athlete_access(
        athlete_id,
        coach,
    )

    deleted = repository.delete(
        athlete_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Atleta não encontrado",
        )
