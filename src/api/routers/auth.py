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

from repositories.invitation_repository import InvitationRepository
from repositories.user_repository import UserRepository
from services.auth.password_reset_service import PasswordResetService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

user_repository = UserRepository()
invitation_repository = InvitationRepository()
password_reset_service = PasswordResetService()

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

    role: Literal[
        "coach",
        "student",
    ] | None = None


class AuthResponse(BaseModel):

    token: str
    user: UserOut


class PendingRegistrationResponse(BaseModel):

    pending_approval: bool
    message: str
    user: UserOut

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

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

    user = user_repository.get_by_id(
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
            detail="Cadastro aguardando aprovação do treinador",
        )

    return user


def validate_student_invitation(
    invite_token: str | None,
    email: str,
):

    if not invite_token:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O cadastro de atleta exige um convite válido",
        )

    invitation = invitation_repository.get_by_token(
        invite_token,
    )

    if invitation is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convite não encontrado",
        )

    if invitation.status != "sent":

        if invitation.status == "pending":

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este convite já possui um cadastro aguardando aprovação",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este convite já foi utilizado",
        )

    invitation_email = invitation.email.strip().lower()

    if (
        invitation_email
        and invitation_email != email
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este convite foi enviado para outro e-mail",
        )

    return invitation


@router.post(
    "/register",
    response_model=AuthResponse | PendingRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
):

    normalized_email = normalize_email(
        payload.email,
    )

    if user_repository.email_exists(
        normalized_email,
    ):

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado",
        )

    if payload.role == "student":

        invitation = validate_student_invitation(
            invite_token=payload.invite_token,
            email=normalized_email,
        )

        user = user_repository.create(
            name=payload.name,
            email=normalized_email,
            password_hash=hash_password(
                payload.password,
            ),
            role="student",
            is_active=False,
        )

        pending_invitation = invitation_repository.mark_pending(
            invitation_id=invitation.id,
            student_user_id=user.id,
            email=normalized_email,
        )

        if pending_invitation is None:

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível vincular o cadastro ao convite",
            )

        return PendingRegistrationResponse(
            pending_approval=True,
            message="Pré-cadastro enviado. Aguarde a aprovação do treinador.",
            user=UserOut.model_validate(
                user,
            ),
        )

    user = user_repository.create(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(
            payload.password,
        ),
        role="coach",
        is_active=True,
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

    user = user_repository.get_by_email(
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

    if (
        payload.role is not None
        and user.role != payload.role
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A conta não corresponde ao perfil selecionado",
        )

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro aguardando aprovação do treinador",
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

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    payload: ForgotPasswordRequest,
):
    normalized_email = normalize_email(
        payload.email,
    )

    reset_token = password_reset_service.request_reset(
        normalized_email,
    )

    response = {
        "message": (
            "Se o e-mail estiver cadastrado, "
            "você receberá as instruções para redefinir a senha."
        ),
    }

    # Temporário para desenvolvimento.
    # Em produção, o token será enviado por e-mail.
    if reset_token is not None:
        response["reset_token"] = reset_token

    return response


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
def reset_password(
    payload: ResetPasswordRequest,
):
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nova senha deve ter pelo menos 8 caracteres",
        )

    if len(payload.password) > 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nova senha deve ter no máximo 128 caracteres",
        )

    changed = password_reset_service.reset_password(
        token=payload.token,
        new_password=payload.password,
    )

    if not changed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O link de recuperação é inválido, "
                "já foi utilizado ou expirou"
            ),
        )

    return {
        "message": (
            "Senha alterada com sucesso. "
            "Faça o login com a nova senha."
        ),
    }

