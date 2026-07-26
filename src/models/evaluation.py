from datetime import date
from datetime import datetime

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.database import Base


class Evaluation(Base):

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athletes.id"),
        nullable=False,
    )

    weight: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    height: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    max_hr: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    resting_hr: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    test_type: Mapped[str] = mapped_column(
        String(30),
        default="NONE",
        nullable=False,
    )

    distance: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    time_seconds: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    vdot: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    test_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )