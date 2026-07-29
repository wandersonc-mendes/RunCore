import smtplib

from email.message import EmailMessage
from email.utils import formataddr

from config import SMTP_FROM_EMAIL
from config import SMTP_FROM_NAME
from config import SMTP_HOST
from config import SMTP_PASSWORD
from config import SMTP_PORT
from config import SMTP_USERNAME
from config import SMTP_USE_TLS


class EmailService:

    @staticmethod
    def is_configured() -> bool:

        return bool(
            SMTP_HOST
            and SMTP_FROM_EMAIL
        )

    def send(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
    ) -> None:

        if not self.is_configured():
            raise RuntimeError(
                "O serviço SMTP não está configurado",
            )

        message = EmailMessage()
        message["From"] = formataddr(
            (
                SMTP_FROM_NAME,
                SMTP_FROM_EMAIL,
            )
        )
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=15,
        ) as smtp:

            if SMTP_USE_TLS:
                smtp.starttls()

            if SMTP_USERNAME:
                smtp.login(
                    SMTP_USERNAME,
                    SMTP_PASSWORD,
                )

            smtp.send_message(
                message,
            )
