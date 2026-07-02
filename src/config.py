from pathlib import Path

APP_NAME = "RunCore"
APP_VERSION = "0.0.6"

BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "runcore.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"