from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database.database import Base


class IptAssessment(Base):

    __tablename__ = "ipt_assessments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athletes.id"),
        nullable=False,
        index=True,
    )

    protocol_id: Mapped[int] = mapped_column(
        ForeignKey("ipt_protocols.id"),
        nullable=False,
        index=True,
    )

    short_result: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    long_result: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    short_speed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    long_speed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    ipt_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    profile: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    interpretation: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    emphasis: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    notes: Mapped[str] = mapped_column(
        String(1000),
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )

    protocol = relationship(
        "IptProtocol",
        back_populates="assessments",
    )