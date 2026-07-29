from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, inspect, select, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQLITE_PATH = (
    PROJECT_ROOT
    / "src"
    / "runcore.db"
)

SQLITE_URL = (
    f"sqlite:///{SQLITE_PATH.as_posix()}"
)

POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


def normalize_postgres_url(url: str) -> str:
    if url.startswith(
        "postgresql://",
    ):
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return url


def count_rows(
    connection,
    table,
) -> int:
    return connection.execute(
        select(
            text("COUNT(*)"),
        ).select_from(
            table,
        ),
    ).scalar_one()


def main() -> None:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"Banco SQLite não encontrado: {SQLITE_PATH}"
        )

    if not POSTGRES_URL:
        raise RuntimeError(
            "A variável DATABASE_URL não foi definida."
        )

    postgres_url = normalize_postgres_url(
        POSTGRES_URL,
    )

    sqlite_engine = create_engine(
        SQLITE_URL,
    )

    postgres_engine = create_engine(
        postgres_url,
        pool_pre_ping=True,
    )

    source_metadata = MetaData()
    source_metadata.reflect(
        bind=sqlite_engine,
    )

    target_metadata = MetaData()
    target_metadata.reflect(
        bind=postgres_engine,
    )

    ignored_tables = {
        "alembic_version",
        "sqlite_sequence",
    }

    source_tables = [
        table
        for table in source_metadata.sorted_tables
        if table.name not in ignored_tables
    ]

    print(
        f"Origem: {SQLITE_PATH}"
    )
    print(
        "Destino: PostgreSQL/Supabase"
    )
    print()

    with (
        sqlite_engine.connect() as source_connection,
        postgres_engine.begin() as target_connection,
    ):
        target_inspector = inspect(
            target_connection,
        )

        for source_table in source_tables:
            table_name = source_table.name

            if not target_inspector.has_table(
                table_name,
            ):
                raise RuntimeError(
                    f"Tabela ausente no PostgreSQL: {table_name}"
                )

            target_table = target_metadata.tables[
                table_name
            ]

            existing_count = target_connection.execute(
                select(
                    text("COUNT(*)"),
                ).select_from(
                    target_table,
                ),
            ).scalar_one()

            if existing_count != 0:
                raise RuntimeError(
                    f"A tabela {table_name} não está vazia: "
                    f"{existing_count} registro(s)."
                )

            source_rows = source_connection.execute(
                select(
                    source_table,
                ),
            ).mappings().all()

            if not source_rows:
                print(
                    f"{table_name}: 0 registros"
                )
                continue

            target_column_names = {
                column.name
                for column in target_table.columns
            }

            rows_to_insert = []

            for row in source_rows:
                converted_row = {
                    key: value
                    for key, value in dict(row).items()
                    if key in target_column_names
                }

                rows_to_insert.append(
                    converted_row,
                )

            target_connection.execute(
                target_table.insert(),
                rows_to_insert,
            )

            print(
                f"{table_name}: "
                f"{len(rows_to_insert)} registro(s) migrado(s)"
            )

        # Atualiza as sequences do PostgreSQL após inserir IDs explícitos.
        sequence_rows = target_connection.execute(
            text(
                """
                SELECT
                    table_name,
                    column_name,
                    pg_get_serial_sequence(
                        quote_ident(table_name),
                        column_name
                    ) AS sequence_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_default LIKE 'nextval(%'
                ORDER BY table_name, ordinal_position
                """
            ),
        ).mappings().all()

        for sequence_row in sequence_rows:
            table_name = sequence_row[
                "table_name"
            ]
            column_name = sequence_row[
                "column_name"
            ]
            sequence_name = sequence_row[
                "sequence_name"
            ]

            if not sequence_name:
                continue

            target_connection.execute(
                text(
                    f"""
                    SELECT setval(
                        :sequence_name,
                        COALESCE(
                            (
                                SELECT MAX("{column_name}")
                                FROM "{table_name}"
                            ),
                            1
                        ),
                        (
                            SELECT COUNT(*) > 0
                            FROM "{table_name}"
                        )
                    )
                    """
                ),
                {
                    "sequence_name": sequence_name,
                },
            )

    print()
    print(
        "Migração concluída com sucesso."
    )


if __name__ == "__main__":
    main()