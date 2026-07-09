from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database.database import Base


class Training(Base):

    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athletes.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
    )

    methodology: Mapped[str] = mapped_column(
        String(50),
        default="Jack Daniels",
    )

    objective: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    target_distance: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    athlete = relationship(
        "Athlete",
        back_populates="trainings",
    )

    sessions = relationship(
        "TrainingSession",
        back_populates="training",
        cascade="all, delete-orphan",
    )