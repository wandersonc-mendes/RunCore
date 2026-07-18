from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class AthleteBase(BaseModel):

    name: str
    phone: str = ""
    email: str = ""
    goal: str = ""
    active: bool = True
    notes: str = ""


class AthleteCreate(AthleteBase):
    pass


class AthleteUpdate(AthleteBase):
    pass


class AthleteOut(AthleteBase):

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EvaluationBase(BaseModel):

    weight: float = 0
    height: float = 0
    max_hr: int = 0
    resting_hr: int = 0
    test_type: str = "Nenhum"
    distance: float = 0
    time_seconds: float = 0


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationOut(EvaluationBase):

    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    vdot: float
    created_at: datetime
