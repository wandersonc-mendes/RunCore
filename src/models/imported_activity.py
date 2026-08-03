from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class ImportedActivity(Base):

    __tablename__ = "imported_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("external_integrations.id"), nullable=False)
    provider_activity_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")
    sport_type: Mapped[str] = mapped_column(String(50), default="")
    distance: Mapped[float] = mapped_column(Float, default=0)
    moving_time: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_elevation_gain: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
