from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from api.routers.auth import get_current_user
from models.user import User


def current_user(
    user: User = Depends(
        get_current_user,
    ),
) -> User:

    return user


def require_coach(
    user: User = Depends(
        current_user,
    ),
) -> User:

    if user.role != "coach":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao treinador.",
        )

    return user