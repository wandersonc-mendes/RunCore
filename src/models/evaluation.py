from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

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
    )

    height: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    max_hr: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    resting_hr: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    vo2: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )