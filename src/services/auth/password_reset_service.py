import hashlib
import secrets

from datetime import datetime
from datetime import timedelta

from api.security import hash_password
from repositories.password_reset_repository import (
    PasswordResetRepository,
)
from repositories.user_repository import UserRepository


RESET_TOKEN_EXPIRE_MINUTES = 30


class PasswordResetService:

    def __init__(self):

        self.users = UserRepository()
        self.tokens = PasswordResetRepository()

    @staticmethod
    def _hash_token(
        token: str,
    ) -> str:

        return hashlib.sha256(
            token.encode("utf-8"),
        ).hexdigest()

    def request_reset(
        self,
        email: str,
    ) -> str | None:

        user = self.users.get_by_email(
            email,
        )

        if user is None:
            return None

        self.tokens.invalidate_for_user(
            user.id,
        )

        token = secrets.token_urlsafe(
            48,
        )

        token_hash = self._hash_token(
            token,
        )

        expires_at = datetime.now() + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES,
        )

        self.tokens.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return token

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> bool:

        token_hash = self._hash_token(
            token,
        )

        reset_token = self.tokens.get_valid_by_hash(
            token_hash,
        )

        if reset_token is None:
            return False

        password_hash = hash_password(
            new_password,
        )

        user = self.users.update_password(
            user_id=reset_token.user_id,
            password_hash=password_hash,
        )

        if user is None:
            return False

        self.tokens.mark_as_used(
            reset_token.id,
        )

        return True