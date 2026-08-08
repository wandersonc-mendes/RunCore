from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.access_control import require_athlete_access
from api.dependencies import current_user, require_coach
from repositories.access_repository import AccessRepository
from repositories.athlete_details_repository import AthleteDetailsRepository
from repositories.athlete_repository import AthleteRepository


router = APIRouter(prefix="/student/profile", tags=["profile"])
access = AccessRepository()
details = AthleteDetailsRepository()
athletes = AthleteRepository()


class ProfilePayload(BaseModel):
    personal: dict = Field(default_factory=dict)
    parq: dict = Field(default_factory=dict)
    training: dict = Field(default_factory=dict)


def athlete_id_for(user):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Perfil disponível apenas para aluno.")
    athlete_id = access.athlete_for_student(user.id)
    if athlete_id is None:
        raise HTTPException(status_code=404, detail="Perfil de atleta não encontrado.")
    return athlete_id


REQUIRED_PERSONAL_FIELDS = {
    "name": "Nome completo",
    "birth_date": "Data de nascimento",
    "sex": "Sexo",
    "phone": "Celular",
    "city": "Cidade",
    "state": "Estado",
}

REQUIRED_TRAINING_FIELDS = {
    "days": "Dias disponíveis",
    "modality": "Modalidade principal",
    "goal": "Objetivo atual",
}


def profile_completion(personal, parq, training):
    missing = []

    for field, label in REQUIRED_PERSONAL_FIELDS.items():
        value = personal.get(field)

        if not value or (
            isinstance(value, str)
            and not value.strip()
        ):
            missing.append(label)

    for index in range(1, 8):
        if parq.get(f"q{index}") not in {
            "Sim",
            "Não",
        }:
            missing.append(f"PAR-Q {index}")

    for field, label in REQUIRED_TRAINING_FIELDS.items():
        value = training.get(field)

        if not value or (
            isinstance(value, str)
            and not value.strip()
        ):
            missing.append(label)

    return {
        "complete": len(missing) == 0,
        "missing_fields": missing,
    }


def serialize(item, athlete=None):
    personal = dict(item.personal) if item else {}
    parq = dict(item.parq) if item else {}
    training = dict(item.training) if item else {}

    if athlete:
        personal.setdefault("name", athlete.name)
        personal.setdefault("email", athlete.email)
        personal.setdefault("phone", athlete.phone)
        personal.setdefault("goal", athlete.goal)

    completion = profile_completion(
        personal,
        parq,
        training,
    )

    return {
        "personal": personal,
        "parq": parq,
        "training": training,
        **completion,
    }


@router.get("")
def get_profile(user=Depends(current_user)):
    athlete_id = athlete_id_for(user)
    return serialize(details.get(athlete_id), athletes.get_by_id(athlete_id))


@router.put("")
def save_profile(payload: ProfilePayload, user=Depends(current_user)):
    athlete_id = athlete_id_for(user)
    athletes.update_phone(athlete_id, payload.personal.get("phone", ""))
    return serialize(details.save(athlete_id, payload.personal, payload.parq, payload.training), athletes.get_by_id(athlete_id))


@router.get("/athletes/{athlete_id}")
def get_athlete_profile(
    athlete_id: int,
    coach=Depends(require_coach),
):
    athlete = require_athlete_access(
        athlete_id,
        coach,
    )

    return serialize(
        details.get(athlete_id),
        athlete,
    )
