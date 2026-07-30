from datetime import date
from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from sqlalchemy.exc import IntegrityError

from api.dependencies import require_admin
from api.security import hash_password
from models.user import User
from repositories.athlete_repository import AthleteRepository
from repositories.user_repository import UserRepository


router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
)

user_repository = UserRepository()
athlete_repository = AthleteRepository()


class ManagedUserOut(BaseModel):

    id: int
    name: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ManagedUserCreate(BaseModel):

    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["coach", "admin"]
    is_active: bool = True


class CoachCreate(BaseModel):

    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    is_active: bool = True
    birth_date: date | None = None
    sex: str = Field(default="", max_length=30)
    cpf: str = Field(default="", max_length=20)
    rg: str = Field(default="", max_length=30)
    team_role: str = Field(default="", max_length=100)
    cref: str = Field(default="", max_length=30)
    instagram: str = Field(default="", max_length=100)
    show_public_profile: bool = True
    photo_url: str = Field(default="", max_length=2_000_000)
    can_view_athletes: bool = True
    can_administer: bool = False
    zip_code: str = Field(default="", max_length=12)
    address: str = Field(default="", max_length=255)
    address_number: str = Field(default="", max_length=20)
    address_extra: str = Field(default="", max_length=120)
    neighborhood: str = Field(default="", max_length=120)
    city: str = Field(default="", max_length=120)
    state: str = Field(default="", max_length=2)
    phone: str = Field(default="", max_length=30)
    phone_secondary: str = Field(default="", max_length=30)
    curriculum: str = Field(default="", max_length=5000)
    notes: str = Field(default="", max_length=5000)


class ManagedUserUpdate(BaseModel):

    name: str = Field(min_length=2, max_length=120)
    role: Literal["coach", "admin", "student"]
    is_active: bool


def normalized_email(value: str) -> str:

    email = value.strip().lower()

    if (
        "@" not in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe um e-mail válido.",
        )

    return email


@router.get(
    "",
    response_model=list[ManagedUserOut],
)
def list_users(
    _: User = Depends(require_admin),
):

    return user_repository.list_all()


@router.post(
    "",
    response_model=ManagedUserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: ManagedUserCreate,
    _: User = Depends(require_admin),
):

    email = normalized_email(payload.email)

    if user_repository.email_exists(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    return user_repository.create(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )


@router.post(
    "/coaches",
    response_model=ManagedUserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_coach(
    payload: CoachCreate,
    _: User = Depends(require_admin),
):

    email = normalized_email(payload.email)

    if user_repository.email_exists(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    profile = payload.model_dump(
        exclude={
            "name",
            "email",
            "password",
            "is_active",
        }
    )

    for field, value in profile.items():
        if isinstance(value, str):
            profile[field] = value.strip()

    return user_repository.create_coach_with_profile(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        is_active=payload.is_active,
        profile=profile,
    )


@router.delete(
    "/{user_id}/student",
    status_code=status.HTTP_200_OK,
)
def delete_student(
    user_id: int,
    master: User = Depends(require_admin),
):
    if master.role != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o usuário Master pode remover alunos.",
        )

    target = user_repository.get_by_id(user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    if target.role != "student":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta ação permite remover apenas usuários do tipo Aluno.",
        )

    try:
        athlete = athlete_repository.get_by_user_id(user_id)

        if athlete is not None:
            athlete_repository.delete(athlete.id)

        if not user_repository.archive_student(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "O aluno possui vínculos que impedem a exclusão definitiva. "
                "Desative o acesso e revise os dados vinculados."
            ),
        ) from error

    return {
        "message": (
            f"Aluno {target.name} removido com sucesso. "
            "O acesso foi revogado e o e-mail original foi liberado."
        ),
        "user_id": user_id,
    }


@router.patch(
    "/{user_id}",
    response_model=ManagedUserOut,
)
def update_user(
    user_id: int,
    payload: ManagedUserUpdate,
    admin: User = Depends(require_admin),
):

    target = user_repository.get_by_id(user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    if target.role == "master":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O acesso Master não pode ser alterado por esta tela.",
        )

    changes_student_profile = (
        target.role == "student"
        and payload.role != "student"
    ) or (
        target.role != "student"
        and payload.role == "student"
    )

    if changes_student_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "O perfil de aluno é definido pelo vínculo com o atleta "
                "e não pode ser convertido manualmente."
            ),
        )

    if user_id == admin.id and (
        payload.role != "admin"
        or not payload.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você não pode remover o próprio acesso administrativo.",
        )

    removes_active_admin = (
        target.role == "admin"
        and target.is_active
        and (
            payload.role != "admin"
            or not payload.is_active
        )
    )

    if (
        removes_active_admin
        and user_repository.count_active_by_role("admin") <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O sistema precisa manter ao menos um administrador ativo.",
        )

    updated = user_repository.update_access(
        user_id,
        name=payload.name,
        role=payload.role,
        is_active=payload.is_active,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    return updated
