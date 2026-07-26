import base64
import hashlib
import hmac
import os

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt

from config import AUTH_ALGORITHM
from config import AUTH_SECRET_KEY
from config import AUTH_TOKEN_EXPIRE_MINUTES


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 210_000


def hash_password(password: str) -> str:

    salt = os.urandom(16)

    password_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    encoded_salt = base64.b64encode(
        salt,
    ).decode("utf-8")

    encoded_digest = base64.b64encode(
        password_digest,
    ).decode("utf-8")

    return (
        f"{PASSWORD_ALGORITHM}"
        f"${PASSWORD_ITERATIONS}"
        f"${encoded_salt}"
        f"${encoded_digest}"
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    try:

        algorithm, iterations, encoded_salt, encoded_digest = (
            password_hash.split("$", 3)
        )

        if algorithm != PASSWORD_ALGORITHM:
            return False

        salt = base64.b64decode(
            encoded_salt,
        )

        expected_digest = base64.b64decode(
            encoded_digest,
        )

        calculated_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(
            calculated_digest,
            expected_digest,
        )

    except (
        ValueError,
        TypeError,
    ):

        return False


def create_access_token(
    user_id: int,
    role: str,
) -> str:

    issued_at = datetime.now(
        timezone.utc,
    )

    expires_at = issued_at + timedelta(
        minutes=AUTH_TOKEN_EXPIRE_MINUTES,
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        AUTH_SECRET_KEY,
        algorithm=AUTH_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict:

    return jwt.decode(
        token,
        AUTH_SECRET_KEY,
        algorithms=[
            AUTH_ALGORITHM,
        ],
    )