import secrets

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from api.routers.auth import get_current_user
from models.user import User
from repositories.athlete_repository import AthleteRepository
from services.strava_service import StravaService


router = APIRouter(
    prefix="/integrations/strava",
    tags=["strava"],
)

athlete_repository = AthleteRepository()
strava_service = StravaService()


def require_student(
    current_user: User,
) -> None:

    if current_user.role != "student":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "A integração com o Strava está "
                "disponível apenas para atletas"
            ),
        )


@router.get(
    "/connect",
)
def connect_strava(
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_student(
        current_user,
    )

    athlete = athlete_repository.get_by_user_id(
        current_user.id,
    )

    if athlete is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil esportivo do atleta não encontrado",
        )

    state = secrets.token_urlsafe(
        32,
    )

    authorization_url = strava_service.build_authorization_url(
        state=state,
        approval_prompt="force",
    )

    return {
        "authorization_url": authorization_url,
        "state": state,
    }