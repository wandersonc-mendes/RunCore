from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database.database import Base


class StravaConnection(Base):

    __tablename__ = "strava_connections"

    __table_args__ = (
        UniqueConstraint(
            "athlete_id",
            name="uq_strava_connections_athlete_id",
        ),
        UniqueConstraint(
            "strava_athlete_id",
            name="uq_strava_connections_strava_athlete_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    athlete_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "athletes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    strava_athlete_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    refresh_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expires_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    scope: Mapped[str] = mapped_column(
        String(255),
        default="",
        nullable=False,
    )

    athlete_firstname: Mapped[str] = mapped_column(
        String(120),
        default="",
        nullable=False,
    )

    athlete_lastname: Mapped[str] = mapped_column(
        String(120),
        default="",
        nullable=False,
    )

    athlete_profile_url: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    athlete = relationship(
        "Athlete",
    )