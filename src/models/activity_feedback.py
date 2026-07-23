from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class ActivityFeedback(Base):
    __tablename__ = "activity_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("imported_activities.id"), unique=True, nullable=False)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), nullable=False)
    perceived_effort: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    feeling: Mapped[str] = mapped_column(String(30), default="")
    pain: Mapped[str] = mapped_column(String(300), default="")
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pre_fatigue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String(1500), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
