from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from api.routers.auth import get_current_user
from models.user import User


router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
)


def require_student(
    current_user: User,
) -> None:

    if current_user.role != "student":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A integração com o Strava está disponível apenas para atletas",
        )


@router.get(
    "/strava/status",
)
def get_strava_status(
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_student(
        current_user,
    )

    return {
        "connected": False,
        "available": False,
        "message": "Integração com o Strava ainda não configurada",
    }