from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class AthleteProfile(Base):

    __tablename__ = "athlete_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), unique=True)
