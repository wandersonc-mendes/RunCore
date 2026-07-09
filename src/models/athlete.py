from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database.database import Base


class Athlete(Base):

    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        default="",
    )

    email: Mapped[str] = mapped_column(
        String(120),
        default="",
    )

    goal: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    notes: Mapped[str] = mapped_column(
        String(1000),
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )

    trainings = relationship(
        "Training",
        back_populates="athlete",
        cascade="all, delete-orphan",
    )