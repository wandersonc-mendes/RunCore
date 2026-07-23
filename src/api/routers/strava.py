from datetime import datetime
from datetime import timedelta
from datetime import timezone

from urllib.parse import urlencode

import jwt

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from fastapi.responses import RedirectResponse

from api.routers.auth import get_current_user

from config import AUTH_ALGORITHM
from config import AUTH_SECRET_KEY
from config import FRONTEND_URL

from models.user import User

from repositories.athlete_repository import AthleteRepository
from repositories.strava_connection_repository import (
    StravaConnectionRepository,
)

from services.strava_service import StravaService


router = APIRouter(
    prefix="/integrations/strava",
    tags=["strava"],
)

athlete_repository = AthleteRepository()

connection_repository = (
    StravaConnectionRepository()
)

strava_service = StravaService()


STATE_EXPIRE_MINUTES = 10


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


def get_student_athlete(
    current_user: User,
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
            detail=(
                "Perfil esportivo do atleta "
                "não encontrado"
            ),
        )

    return athlete


def create_oauth_state(
    user_id: int,
    athlete_id: int,
) -> str:

    now = datetime.now(
        timezone.utc,
    )

    payload = {
        "purpose": "strava_oauth",
        "user_id": user_id,
        "athlete_id": athlete_id,
        "iat": now,
        "exp": now + timedelta(
            minutes=STATE_EXPIRE_MINUTES,
        ),
    }

    return jwt.encode(
        payload,
        AUTH_SECRET_KEY,
        algorithm=AUTH_ALGORITHM,
    )


def decode_oauth_state(
    state_token: str,
) -> dict:

    try:

        payload = jwt.decode(
            state_token,
            AUTH_SECRET_KEY,
            algorithms=[
                AUTH_ALGORITHM,
            ],
        )

    except jwt.InvalidTokenError as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Estado OAuth inválido ou expirado"
            ),
        ) from error

    if payload.get("purpose") != "strava_oauth":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado OAuth inválido",
        )

    try:

        payload["user_id"] = int(
            payload["user_id"],
        )

        payload["athlete_id"] = int(
            payload["athlete_id"],
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado OAuth incompleto",
        ) from error

    return payload


def frontend_redirect(
    result: str,
    message: str = "",
) -> RedirectResponse:

    parameters = {
        "strava": result,
    }

    if message:
        parameters["message"] = message

    url = (
        f"{FRONTEND_URL}/"
        f"?{urlencode(parameters)}"
    )

    return RedirectResponse(
        url=url,
        status_code=status.HTTP_302_FOUND,
    )


def refresh_connection_if_needed(
    connection,
):

    now_timestamp = int(
        datetime.now(
            timezone.utc,
        ).timestamp()
    )

    if connection.expires_at > (
        now_timestamp + 60
    ):

        return connection

    token_payload = strava_service.refresh_tokens(
        connection.refresh_token,
    )

    access_token = token_payload.get(
        "access_token",
    )

    refresh_token = token_payload.get(
        "refresh_token",
    )

    expires_at = token_payload.get(
        "expires_at",
    )

    if (
        not access_token
        or not refresh_token
        or not expires_at
    ):

        raise RuntimeError(
            "O Strava retornou tokens incompletos"
        )

    updated_connection = (
        connection_repository.update_tokens(
            athlete_id=connection.athlete_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=int(expires_at),
        )
    )

    if updated_connection is None:

        raise RuntimeError(
            "Não foi possível atualizar os tokens"
        )

    return updated_connection


def connection_to_status(
    connection,
) -> dict:

    full_name = " ".join(
        part
        for part in [
            connection.athlete_firstname,
            connection.athlete_lastname,
        ]
        if part
    ).strip()

    return {
        "connected": True,
        "configured": True,
        "available": True,
        "strava_athlete_id": (
            connection.strava_athlete_id
        ),
        "athlete_name": full_name,
        "athlete_profile_url": (
            connection.athlete_profile_url
        ),
        "scope": connection.scope,
        "expires_at": connection.expires_at,
        "connected_at": connection.connected_at,
        "updated_at": connection.updated_at,
        "last_sync_at": connection.last_sync_at,
    }


@router.get(
    "/connect",
)
def connect_strava(
    current_user: User = Depends(
        get_current_user,
    ),
):

    athlete = get_student_athlete(
        current_user,
    )

    state_token = create_oauth_state(
        user_id=current_user.id,
        athlete_id=athlete.id,
    )

    authorization_url = (
        strava_service.build_authorization_url(
            state=state_token,
            approval_prompt="force",
        )
    )

    return {
        "authorization_url": authorization_url,
    }


@router.get(
    "/callback",
)
def strava_callback(
    code: str | None = Query(
        default=None,
    ),
    scope: str | None = Query(
        default=None,
    ),
    state: str | None = Query(
        default=None,
    ),
    error: str | None = Query(
        default=None,
    ),
):

    if error:

        return frontend_redirect(
            result="denied",
            message=(
                "A autorização do Strava "
                "foi cancelada"
            ),
        )

    if not state:

        return frontend_redirect(
            result="error",
            message="Estado OAuth não informado",
        )

    try:

        state_payload = decode_oauth_state(
            state,
        )

        if not code:

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Código de autorização "
                    "não informado"
                ),
            )

        athlete = athlete_repository.get_by_id(
            state_payload["athlete_id"],
        )

        if athlete is None:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Perfil esportivo não encontrado"
                ),
            )

        if athlete.user_id != state_payload["user_id"]:

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "O perfil esportivo não pertence "
                    "ao usuário autenticado"
                ),
            )

        token_payload = (
            strava_service.exchange_code_for_tokens(
                code,
            )
        )

        access_token = token_payload.get(
            "access_token",
        )

        refresh_token = token_payload.get(
            "refresh_token",
        )

        expires_at = token_payload.get(
            "expires_at",
        )

        strava_athlete = token_payload.get(
            "athlete",
        ) or {}

        strava_athlete_id = (
            strava_athlete.get("id")
        )

        if (
            not access_token
            or not refresh_token
            or not expires_at
            or not strava_athlete_id
        ):

            raise RuntimeError(
                "O Strava retornou dados "
                "de autenticação incompletos"
            )

        existing_connection = (
            connection_repository
            .get_by_strava_athlete_id(
                int(strava_athlete_id),
            )
        )

        if (
            existing_connection is not None
            and existing_connection.athlete_id
            != athlete.id
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Esta conta do Strava já está "
                    "vinculada a outro atleta"
                ),
            )

        granted_scope = (
            token_payload.get("scope")
            or scope
            or ""
        )

        profile_url = (
            strava_athlete.get(
                "profile_medium",
            )
            or strava_athlete.get(
                "profile",
            )
            or ""
        )

        connection_repository.create_or_update(
            athlete_id=athlete.id,
            strava_athlete_id=int(
                strava_athlete_id,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=int(expires_at),
            scope=granted_scope,
            athlete_firstname=(
                strava_athlete.get(
                    "firstname",
                )
                or ""
            ),
            athlete_lastname=(
                strava_athlete.get(
                    "lastname",
                )
                or ""
            ),
            athlete_profile_url=profile_url,
        )

        return frontend_redirect(
            result="connected",
            message=(
                "Conta do Strava conectada "
                "com sucesso"
            ),
        )

    except HTTPException as error_response:

        return frontend_redirect(
            result="error",
            message=str(
                error_response.detail,
            ),
        )

    except Exception as error_response:

        return frontend_redirect(
            result="error",
            message=str(
                error_response,
            ),
        )


@router.get(
    "/status",
)
def get_strava_status(
    current_user: User = Depends(
        get_current_user,
    ),
):

    athlete = get_student_athlete(
        current_user,
    )

    connection = (
        connection_repository.get_by_athlete_id(
            athlete.id,
        )
    )

    if connection is None:

        return {
            "connected": False,
            "configured": True,
            "available": True,
            "message": (
                "Conecte sua conta do Strava "
                "para importar suas atividades"
            ),
        }

    try:

        connection = refresh_connection_if_needed(
            connection,
        )

    except Exception as error:

        return {
            "connected": False,
            "configured": True,
            "available": True,
            "requires_reconnection": True,
            "message": str(error),
        }

    return connection_to_status(
        connection,
    )


@router.post(
    "/disconnect",
)
def disconnect_strava(
    current_user: User = Depends(
        get_current_user,
    ),
):

    athlete = get_student_athlete(
        current_user,
    )

    connection = (
        connection_repository.get_by_athlete_id(
            athlete.id,
        )
    )

    if connection is None:

        return {
            "disconnected": True,
            "message": (
                "Nenhuma conta do Strava "
                "estava conectada"
            ),
        }

    try:

        strava_service.revoke_token(
            token=connection.refresh_token,
            token_type_hint="refresh_token",
        )

    except Exception as error:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    deleted = (
        connection_repository.delete_by_athlete_id(
            athlete.id,
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "O acesso foi revogado no Strava, "
                "mas não foi possível remover a "
                "conexão local"
            ),
        )

    return {
        "disconnected": True,
        "message": (
            "Conta do Strava desconectada "
            "com sucesso"
        ),
    }