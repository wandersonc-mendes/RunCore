from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from pydantic import BaseModel

from api.routers.auth import get_current_user

from models.user import User

from repositories.invitation_repository import InvitationRepository


router = APIRouter(
    prefix="/coach",
    tags=["coach"],
)

repository = InvitationRepository()


class InvitationCreate(BaseModel):

    email: str = ""


def require_coach(
    current_user: User,
) -> None:

    if current_user.role != "coach":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente para treinadores",
        )


def build_registration_url(
    request: Request,
    token: str,
) -> str:

    base_url = str(
        request.base_url,
    ).rstrip("/")

    return (
        f"{base_url}/"
        f"?invite={token}"
    )


def invitation_to_dict(
    invitation,
    request: Request,
) -> dict:

    return {
        "id": invitation.id,
        "email": invitation.email,
        "status": invitation.status,
        "token": invitation.token,
        "created_at": invitation.created_at,
        "approved_at": invitation.approved_at,
        "registration_url": build_registration_url(
            request,
            invitation.token,
        ),
    }


@router.get(
    "/invitations",
)
def list_invitations(
    request: Request,
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_coach(
        current_user,
    )

    invitations = repository.list_by_coach(
        current_user.id,
    )

    sent = [
        invitation_to_dict(
            invitation,
            request,
        )
        for invitation in invitations
        if invitation.status == "sent"
    ]

    pending = [
        invitation_to_dict(
            invitation,
            request,
        )
        for invitation in invitations
        if invitation.status == "pending"
    ]

    return {
        "pending": pending,
        "sent": sent,
    }


@router.post(
    "/invitations",
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    payload: InvitationCreate,
    request: Request,
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_coach(
        current_user,
    )

    invitation = repository.create(
        coach_user_id=current_user.id,
        email=payload.email,
    )

    return invitation_to_dict(
        invitation,
        request,
    )