from datetime import date
from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AthleteBase(BaseModel):

    name: str
    phone: str = ""
    email: str = ""
    goal: str = ""
    active: bool = True
    notes: str = ""


class AuthRegister(BaseModel):

    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)
    role: Literal["coach", "student"]
    invite_token: str | None = None


class AuthLogin(BaseModel):

    email: str
    password: str


class UserOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class AuthResponse(BaseModel):

    token: str
    user: UserOut


class AthleteCreate(AthleteBase):
    pass


class AthleteUpdate(AthleteBase):
    pass


class AthleteOut(AthleteBase):

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EvaluationCreate(BaseModel):

    weight: float = Field(
        ge=20,
        le=300,
    )

    height: float = Field(
        ge=0.8,
        le=2.5,
    )

    max_hr: int = Field(
        ge=80,
        le=250,
    )

    resting_hr: int = Field(
        ge=30,
        le=150,
    )

    test_type: Literal[
        "3 km",
        "5 km",
        "10 km",
        "Meia maratona",
        "Maratona",
    ]

    time: str = Field(
        min_length=7,
        max_length=8,
        pattern=r"^\d{1,2}:\d{2}:\d{2}$",
    )

    test_date: date


class EvaluationOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    weight: float
    height: float
    max_hr: int
    resting_hr: int
    test_type: str
    distance: float
    time_seconds: float
    vdot: float
    test_date: date | None
    created_at: datetime


class TrainingSessionOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    week: int
    weekday: int
    workout_name: str
    zone: str
    planned_distance: float
    repetitions: int
    recovery: int
    completed: bool
    session_date: date | None = None
    phase: str = "Base"
    adaptations: list[str] = []
    steps: list["TrainingStepOut"]


class TrainingStepOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    order: int
    type: str
    distance: float
    distance_unit: str = "km"
    repetitions: int
    recovery: str
    pace_min: str
    pace_max: str
    notes: str


class TrainingOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    name: str
    methodology: str
    objective: str
    target_distance: float
    start_date: date | None = None
    target_date: date | None = None
    total_weeks: int = 0
    current_week: int = 1
    current_phase: str = "Base"
    active: bool
    sessions: list[TrainingSessionOut]


class TrainingCreate(BaseModel):

    name: str = Field(
        default="Planejamento Principal",
        min_length=2,
        max_length=100,
    )

    objective: str = Field(
        default="Desenvolvimento",
        min_length=2,
        max_length=100,
    )

    target_distance: float = Field(
        gt=0,
        le=500,
    )

    start_date: date
    target_date: date | None = None

    total_weeks: int | None = Field(
        default=None,
        ge=4,
        le=52,
    )


class TrainingSessionUpdate(BaseModel):

    session_date: date | None = None

    workout_name: str = Field(
        min_length=2,
        max_length=80,
    )

    zone: str = Field(
        min_length=2,
        max_length=30,
    )

    planned_distance: float = Field(
        ge=0,
        le=1000,
    )

    repetitions: int = Field(
        ge=0,
        le=100,
    )

    notes: str = Field(
        default="",
        max_length=1000,
    )

    steps: list["TrainingStepUpdate"] = Field(
        default_factory=list,
        min_length=1,
        max_length=20,
    )


class TrainingStepUpdate(BaseModel):

    type: str = Field(
        min_length=2,
        max_length=30,
    )

    distance: float = Field(
        ge=0,
        le=1000,
    )

    distance_unit: Literal["km", "m"] = "km"

    repetitions: int = Field(
        ge=0,
        le=100,
    )

    recovery: str = Field(
        default="",
        max_length=80,
    )

    pace_min: str = Field(
        default="",
        max_length=10,
    )

    pace_max: str = Field(
        default="",
        max_length=10,
    )

    notes: str = Field(
        default="",
        max_length=2000,
    )


class ActivityFeedbackPayload(BaseModel):

    perceived_effort: int = Field(
        ge=1,
        le=10,
    )

    feeling: Literal[
        "otimo",
        "bem",
        "pesado",
        "muito_dificil",
    ] = "bem"

    pain: str = Field(
        default="",
        max_length=300,
    )

    sleep_quality: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    pre_fatigue: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    notes: str = Field(
        default="",
        max_length=1500,
    )

class IptProtocolOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    protocol_type: str
    short_value: float
    long_value: float
    input_mode: str
    active: bool


class IptAssessmentCreate(BaseModel):

    protocol_id: int = Field(gt=0)
    short_result: float = Field(gt=0)
    long_result: float = Field(gt=0)
    notes: str = Field(
        default="",
        max_length=1000,
    )


class IptAssessmentOut(BaseModel):

    id: int
    athlete_id: int
    protocol_id: int
    protocol_code: str
    protocol_name: str
    short_result: float
    long_result: float
    short_speed: float
    long_speed: float
    ipt_percentage: float
    profile: str
    interpretation: str
    emphasis: str
    notes: str
    created_at: datetime