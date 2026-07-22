from typing import Literal

import jwt

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from api.security import create_access_token
from api.security import decode_access_token
from api.security import hash_password
from api.security import verify_password

from models.user import User

from repositories.user_repository import UserRepository


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

repository = UserRepository()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


class UserOut(BaseModel):

    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: str = Field(
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: Literal[
        "coach",
        "student",
    ] = "coach"

    invite_token: str | None = None


class LoginRequest(BaseModel):

    email: str = Field(
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: str | None = None


class AuthResponse(BaseModel):

    token: str
    user: UserOut


def normalize_email(
    email: str,
) -> str:

    normalized_email = email.strip().lower()

    if (
        "@" not in normalized_email
        or normalized_email.startswith("@")
        or normalized_email.endswith("@")
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe um e-mail válido",
        )

    return normalized_email


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
) -> User:

    if credentials is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    try:

        payload = decode_access_token(
            credentials.credentials,
        )

        user_id = int(
            payload["sub"],
        )

    except (
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    user = repository.get_by_id(
        user_id,
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return user


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
):

    normalized_email = normalize_email(
        payload.email,
    )

    if repository.email_exists(
        normalized_email,
    ):

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado",
        )

    user = repository.create(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(
            payload.password,
        ),
        role=payload.role,
    )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return AuthResponse(
        token=token,
        user=UserOut.model_validate(
            user,
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    payload: LoginRequest,
):

    normalized_email = normalize_email(
        payload.email,
    )

    user = repository.get_by_email(
        normalized_email,
    )

    if (
        user is None
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return AuthResponse(
        token=token,
        user=UserOut.model_validate(
            user,
        ),
    )


@router.get(
    "/me",
    response_model=UserOut,
)
def get_me(
    current_user: User = Depends(
        get_current_user,
    ),
):

    return current_user