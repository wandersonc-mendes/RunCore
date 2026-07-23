import os
from pathlib import Path

from dotenv import load_dotenv


APP_NAME = "RunCore"
APP_VERSION = "0.0.7"


BASE_DIR = Path(__file__).resolve().parent
WEB_PROJECT_DIR = BASE_DIR.parent
ROOT_PROJECT_DIR = WEB_PROJECT_DIR.parent


ENV_FILE = WEB_PROJECT_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
)


# ==========================
# Banco de dados
# ==========================

DATABASE_FILE = ROOT_PROJECT_DIR / "src" / "runcore.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"


# ==========================
# Aplicação
# ==========================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "https://runcore.tailf3239d.ts.net",
).rstrip("/")

PUBLIC_FRONTEND_URL = FRONTEND_URL


ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        FRONTEND_URL,
    ).split(",")
    if origin.strip()
]


# ==========================
# Autenticação
# ==========================

AUTH_SECRET_KEY = os.getenv(
    "AUTH_SECRET",
    "runcore-dev-secret-change-in-production",
)

AUTH_ALGORITHM = "HS256"

AUTH_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "AUTH_TOKEN_EXPIRE_MINUTES",
        "720",
    )
)


# ==========================
# Strava
# ==========================

STRAVA_CLIENT_ID = os.getenv(
    "STRAVA_CLIENT_ID",
    "",
).strip()

STRAVA_CLIENT_SECRET = os.getenv(
    "STRAVA_CLIENT_SECRET",
    "",
).strip()

STRAVA_REDIRECT_URI = os.getenv(
    "STRAVA_REDIRECT_URI",
    (
        f"{FRONTEND_URL}"
        "/api/integrations/strava/callback"
    ),
).strip()


def validate_strava_configuration() -> None:

    missing = []

    if not STRAVA_CLIENT_ID:
        missing.append(
            "STRAVA_CLIENT_ID",
        )

    if not STRAVA_CLIENT_SECRET:
        missing.append(
            "STRAVA_CLIENT_SECRET",
        )

    if not STRAVA_REDIRECT_URI:
        missing.append(
            "STRAVA_REDIRECT_URI",
        )

    if missing:
        raise RuntimeError(
            "Configuração do Strava incompleta: "
            + ", ".join(missing)
        )