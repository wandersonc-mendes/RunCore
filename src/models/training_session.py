from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.database import Base


class TrainingSession(Base):

    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    training_id: Mapped[int] = mapped_column(
        ForeignKey("trainings.id"),
        nullable=False,
    )

    week: Mapped[int] = mapped_column(
        Integer,
    )

    weekday: Mapped[int] = mapped_column(
        Integer,
    )

    workout_name: Mapped[str] = mapped_column(
        String(80),
    )

    zone: Mapped[str] = mapped_column(
        String(30),
    )

    planned_distance: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    completed_distance: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    planned_duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completed_duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    repetitions: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    recovery: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    rpe: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    notes: Mapped[str] = mapped_column(
        String(1000),
        default="",
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    training = relationship(
        "Training",
        back_populates="sessions",
    )