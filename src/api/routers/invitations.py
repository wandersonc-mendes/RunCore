from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from pydantic import BaseModel

from api.routers.auth import get_current_user

from config import PUBLIC_FRONTEND_URL

from models.user import User

from repositories.invitation_repository import InvitationRepository
from repositories.user_repository import UserRepository


router = APIRouter(
    prefix="/coach",
    tags=["coach"],
)

invitation_repository = InvitationRepository()
user_repository = UserRepository()


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
    token: str,
) -> str:

    return (
        f"{PUBLIC_FRONTEND_URL}/"
        f"?invite={token}"
    )


def invitation_to_dict(
    invitation,
) -> dict:

    return {
        "id": invitation.id,
        "email": invitation.email,
        "status": invitation.status,
        "token": invitation.token,
        "student_user_id": invitation.student_user_id,
        "created_at": invitation.created_at,
        "approved_at": invitation.approved_at,
        "registration_url": build_registration_url(
            invitation.token,
        ),
    }


@router.get(
    "/invitations",
)
def list_invitations(
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_coach(
        current_user,
    )

    invitations = invitation_repository.list_by_coach(
        current_user.id,
    )

    sent = [
        invitation_to_dict(
            invitation,
        )
        for invitation in invitations
        if invitation.status == "sent"
    ]

    pending = [
        invitation_to_dict(
            invitation,
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
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_coach(
        current_user,
    )

    invitation = invitation_repository.create(
        coach_user_id=current_user.id,
        email=payload.email,
    )

    return invitation_to_dict(
        invitation,
    )


@router.post(
    "/invitations/{invitation_id}/approve",
)
def approve_invitation(
    invitation_id: int,
    current_user: User = Depends(
        get_current_user,
    ),
):

    require_coach(
        current_user,
    )

    invitation = invitation_repository.get_by_id(
        invitation_id,
    )

    if invitation is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convite não encontrado",
        )

    if invitation.coach_user_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este convite pertence a outro treinador",
        )

    if invitation.status != "pending":

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este convite não está aguardando aprovação",
        )

    if invitation.student_user_id is None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O convite não possui um atleta vinculado",
        )

    student = user_repository.get_by_id(
        invitation.student_user_id,
    )

    if student is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário atleta não encontrado",
        )

    if student.role != "student":

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O usuário vinculado não é um atleta",
        )

    activated_student = user_repository.activate(
        student.id,
    )

    if activated_student is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível ativar o atleta",
        )

    approved_invitation = invitation_repository.approve(
        invitation_id=invitation.id,
        student_user_id=student.id,
    )

    if approved_invitation is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível aprovar o convite",
        )

    return {
        "message": "Atleta aprovado com sucesso",
        "invitation": invitation_to_dict(
            approved_invitation,
        ),
        "user": {
            "id": activated_student.id,
            "name": activated_student.name,
            "email": activated_student.email,
            "role": activated_student.role,
            "is_active": activated_student.is_active,
        },
    }