import os
from pathlib import Path

APP_NAME = "RunCore"
APP_VERSION = "0.0.6"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]

# A versão web utiliza o mesmo banco do aplicativo desktop.
DATABASE_FILE = PROJECT_DIR / "src" / "runcore.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# ==========================
# Endereço público
# ==========================

PUBLIC_FRONTEND_URL = os.getenv(
    "RUNCORE_PUBLIC_FRONTEND_URL",
    "https://notewifi6.tailf3239d.ts.net",
).rstrip("/")

# ==========================
# Autenticação
# ==========================

AUTH_SECRET_KEY = os.getenv(
    "RUNCORE_AUTH_SECRET",
    "runcore-dev-secret-change-in-production",
)

AUTH_ALGORITHM = "HS256"

AUTH_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "RUNCORE_TOKEN_EXPIRE_MINUTES",
        "720",
    )
)