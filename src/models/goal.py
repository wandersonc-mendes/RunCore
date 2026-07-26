from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    distance: Mapped[float] = mapped_column(Float)
    target_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="Principal")
    status: Mapped[str] = mapped_column(String(20), default="Em andamento")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
