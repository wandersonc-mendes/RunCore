from datetime import datetime

from sqlalchemy import select

from database.database import SessionLocal
from models.password_reset_token import PasswordResetToken


class PasswordResetRepository:

    def has_recent_request(
        self,
        user_id: int,
        since: datetime,
    ) -> bool:

        with SessionLocal() as session:

            statement = select(
                PasswordResetToken.id
            ).where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.created_at >= since,
            ).limit(1)

            return session.scalar(statement) is not None

    def create(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:

        with SessionLocal() as session:

            reset_token = PasswordResetToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )

            session.add(reset_token)
            session.commit()
            session.refresh(reset_token)

            return reset_token

    def get_valid_by_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:

        now = datetime.now()

        with SessionLocal() as session:

            statement = select(
                PasswordResetToken
            ).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )

            return session.scalar(statement)

    def invalidate_for_user(
        self,
        user_id: int,
    ) -> None:

        now = datetime.now()

        with SessionLocal() as session:

            statement = select(
                PasswordResetToken
            ).where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )

            tokens = session.scalars(statement).all()

            for token in tokens:
                token.used_at = now

            session.commit()

    def mark_as_used(
        self,
        token_id: int,
    ) -> PasswordResetToken | None:

        with SessionLocal() as session:

            reset_token = session.get(
                PasswordResetToken,
                token_id,
            )

            if reset_token is None:
                return None

            reset_token.used_at = datetime.now()

            session.commit()
            session.refresh(reset_token)

            return reset_token
