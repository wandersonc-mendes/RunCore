from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_FILE = PROJECT_ROOT / "alembic.ini"


def initialize_database() -> None:
    """
    Atualiza o banco até a revisão mais recente do Alembic.

    Em um banco novo, cria todo o schema por meio da migration inicial.
    Em um banco existente e já marcado, aplica somente migrations pendentes.
    """

    if not ALEMBIC_INI_FILE.exists():
        raise FileNotFoundError(
            f"Configuração do Alembic não encontrada: "
            f"{ALEMBIC_INI_FILE}"
        )

    alembic_config = Config(
        str(ALEMBIC_INI_FILE),
    )

    # Evita dependência do diretório em que o comando foi iniciado.
    alembic_config.set_main_option(
        "script_location",
        str(PROJECT_ROOT / "migrations"),
    )

    command.upgrade(
        alembic_config,
        "head",
    )