import sqlite3
from pathlib import Path


DATABASE_FILE = Path(r"D:\RunCore3\src\runcore.db")

LEGACY_TABLES = {
    "coach_invitations",
    "strava_connections",
}


def print_rows(
    connection: sqlite3.Connection,
    table_name: str,
) -> None:
    print()
    print("=" * 80)
    print(table_name.upper())
    print("=" * 80)

    columns = [
        row[1]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        )
    ]

    print("COLUNAS:")
    print(", ".join(columns))

    rows = connection.execute(
        f"SELECT * FROM {table_name} ORDER BY 1"
    ).fetchall()

    print(f"\nREGISTROS: {len(rows)}")

    for row in rows:
        print(dict(zip(columns, row)))


def print_foreign_key_references(
    connection: sqlite3.Connection,
) -> None:
    print()
    print("=" * 80)
    print("CHAVES ESTRANGEIRAS QUE APONTAM PARA TABELAS LEGADAS")
    print("=" * 80)

    tables = [
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
    ]

    references_found = False

    for table_name in tables:
        foreign_keys = connection.execute(
            f"PRAGMA foreign_key_list({table_name})"
        ).fetchall()

        for foreign_key in foreign_keys:
            referenced_table = foreign_key[2]

            if referenced_table not in LEGACY_TABLES:
                continue

            references_found = True

            print(
                {
                    "source_table": table_name,
                    "source_column": foreign_key[3],
                    "referenced_table": referenced_table,
                    "referenced_column": foreign_key[4],
                }
            )

    if not references_found:
        print("Nenhuma tabela aponta para as tabelas legadas.")


def print_current_tables(
    connection: sqlite3.Connection,
) -> None:
    for table_name in (
        "invitations",
        "external_integrations",
    ):
        print_rows(
            connection,
            table_name,
        )


def main() -> None:
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Banco não encontrado: {DATABASE_FILE}"
        )

    connection = sqlite3.connect(
        DATABASE_FILE,
    )

    try:
        for table_name in sorted(
            LEGACY_TABLES
        ):
            print_rows(
                connection,
                table_name,
            )

        print_current_tables(
            connection,
        )

        print_foreign_key_references(
            connection,
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()