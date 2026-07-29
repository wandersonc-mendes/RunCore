from datetime import date

from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.database import Base


class CoachProfile(Base):

    __tablename__ = "coach_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    cpf: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    rg: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    team_role: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    cref: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    instagram: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    show_public_profile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    photo_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    can_view_athletes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    can_administer: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    zip_code: Mapped[str] = mapped_column(String(12), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    address_number: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    address_extra: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    neighborhood: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    phone_secondary: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    curriculum: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
