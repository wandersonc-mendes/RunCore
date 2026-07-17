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
