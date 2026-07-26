from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class CoachAthlete(Base):

    __tablename__ = "coach_athletes"

    coach_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), primary_key=True)
