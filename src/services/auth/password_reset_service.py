import hashlib
import logging
import secrets

from datetime import datetime
from datetime import timedelta
from urllib.parse import urlencode

from api.security import hash_password
from config import PUBLIC_FRONTEND_URL
from repositories.password_reset_repository import (
    PasswordResetRepository,
)
from repositories.user_repository import UserRepository
from services.email_service import EmailService


RESET_TOKEN_EXPIRE_MINUTES = 30
RESET_REQUEST_COOLDOWN_SECONDS = 60

logger = logging.getLogger(__name__)


class PasswordResetService:

    def __init__(
        self,
        email_service: EmailService | None = None,
    ):

        self.users = UserRepository()
        self.tokens = PasswordResetRepository()
        self.email = email_service or EmailService()

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
    ) -> None:

        user = self.users.get_by_email(
            email,
        )

        if user is None:
            return

        cooldown_start = datetime.now() - timedelta(
            seconds=RESET_REQUEST_COOLDOWN_SECONDS,
        )

        if self.tokens.has_recent_request(
            user.id,
            cooldown_start,
        ):
            return

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

        reset_url = (
            f"{PUBLIC_FRONTEND_URL}/?"
            + urlencode(
                {
                    "reset_token": token,
                }
            )
        )

        try:
            self.email.send(
                recipient=user.email,
                subject="Redefinição de senha do RunCore",
                text=(
                    f"Olá, {user.name}.\n\n"
                    "Recebemos uma solicitação para redefinir "
                    "a senha da sua conta RunCore.\n\n"
                    f"Acesse este link: {reset_url}\n\n"
                    f"O link expira em {RESET_TOKEN_EXPIRE_MINUTES} "
                    "minutos e pode ser usado apenas uma vez.\n\n"
                    "Se você não solicitou a alteração, ignore "
                    "este e-mail. Sua senha continuará a mesma."
                ),
            )
        except Exception:
            self.tokens.invalidate_for_user(
                user.id,
            )
            logger.exception(
                "Falha ao enviar e-mail de recuperação de senha",
            )

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

        try:
            self.email.send(
                recipient=user.email,
                subject="Senha do RunCore alterada",
                text=(
                    f"Olá, {user.name}.\n\n"
                    "A senha da sua conta RunCore foi alterada.\n\n"
                    "Se você não fez essa alteração, entre em "
                    "contato imediatamente com a administração."
                ),
            )
        except Exception:
            logger.exception(
                "Falha ao enviar aviso de alteração de senha",
            )

        return True
