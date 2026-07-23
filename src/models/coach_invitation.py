from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class CoachInvitation(Base):
    __tablename__ = "coach_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    email: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(20), default="sent")
    student_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    athlete_id: Mapped[int | None] = mapped_column(ForeignKey("athletes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
