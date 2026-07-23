from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class AthleteDetails(Base):
    __tablename__ = "athlete_details"

    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), primary_key=True)
    personal: Mapped[dict] = mapped_column(JSON, default=dict)
    parq: Mapped[dict] = mapped_column(JSON, default=dict)
    training: Mapped[dict] = mapped_column(JSON, default=dict)
