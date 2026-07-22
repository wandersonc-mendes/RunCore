from pathlib import Path

APP_NAME = "RunCore"
APP_VERSION = "0.0.6"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]

# A versao web utiliza o mesmo banco do aplicativo desktop.
DATABASE_FILE = PROJECT_DIR / "src" / "runcore.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
