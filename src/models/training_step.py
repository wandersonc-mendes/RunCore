from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class TrainingStep(Base):

    __tablename__ = "training_steps"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("training_sessions.id"),
        nullable=False,
    )

    order: Mapped[int] = mapped_column(
        Integer,
    )

    type: Mapped[str] = mapped_column(
        String(30),
    )

    distance: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    distance_unit: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    repetitions: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    recovery: Mapped[str] = mapped_column(
        String(80),
        default="",
    )

    pace_min: Mapped[str] = mapped_column(
        String(10),
        default="",
    )

    pace_max: Mapped[str] = mapped_column(
        String(10),
        default="",
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default="",
    )