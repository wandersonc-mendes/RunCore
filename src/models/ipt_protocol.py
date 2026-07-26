from sqlalchemy import Boolean
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database.database import Base


class IptProtocol(Base):

    __tablename__ = "ipt_protocols"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    protocol_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    short_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    long_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    input_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    assessments = relationship(
        "IptAssessment",
        back_populates="protocol",
        cascade="all, delete-orphan",
    )