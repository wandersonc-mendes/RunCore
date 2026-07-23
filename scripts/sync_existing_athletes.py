import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)

from config import DATABASE_FILE  # noqa: E402


def create_backup(
    database_path: Path,
) -> Path:

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S",
    )

    backup_path = database_path.with_name(
        f"{database_path.stem}.backup-sync-{timestamp}{database_path.suffix}"
    )

    shutil.copy2(
        database_path,
        backup_path,
    )

    return backup_path


def main() -> None:

    database_path = Path(
        DATABASE_FILE,
    )

    if not database_path.exists():
        raise FileNotFoundError(
            f"Banco não encontrado: {database_path}"
        )

    backup_path = create_backup(
        database_path,
    )

    print(
        f"Backup criado: {backup_path}"
    )

    connection = sqlite3.connect(
        database_path,
    )

    try:
        cursor = connection.cursor()

        # Perfis antigos identificados no banco:
        #
        # athlete 1 -> user 2
        # athlete 2 -> user 3
        # athlete 3 -> user 5
        #
        # Todos vinculados ao treinador user 1.

        legacy_links = [
            (2, 1, 1),
            (3, 1, 2),
            (5, 1, 3),
        ]

        for (
            user_id,
            coach_user_id,
            athlete_id,
        ) in legacy_links:

            cursor.execute(
                """
                UPDATE athletes
                SET
                    user_id = ?,
                    coach_user_id = ?
                WHERE id = ?
                """,
                (
                    user_id,
                    coach_user_id,
                    athlete_id,
                ),
            )

        # Atualiza perfis que já existam, usando o treinador
        # registrado no convite aprovado.

        cursor.execute(
            """
            UPDATE athletes
            SET coach_user_id = (
                SELECT invitations.coach_user_id
                FROM invitations
                WHERE
                    invitations.student_user_id = athletes.user_id
                    AND invitations.status = 'approved'
                ORDER BY invitations.id DESC
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM invitations
                WHERE
                    invitations.student_user_id = athletes.user_id
                    AND invitations.status = 'approved'
            )
            """
        )

        # Cria os perfis dos usuários aprovados que ainda
        # não possuem registro na tabela athletes.

        cursor.execute(
            """
            INSERT INTO athletes (
                user_id,
                coach_user_id,
                name,
                phone,
                email,
                goal,
                active,
                notes,
                created_at
            )
            SELECT
                users.id,
                invitations.coach_user_id,
                users.name,
                '',
                users.email,
                '',
                1,
                'Cadastro sincronizado após aprovação.',
                CURRENT_TIMESTAMP
            FROM invitations
            INNER JOIN users
                ON users.id = invitations.student_user_id
            WHERE
                invitations.status = 'approved'
                AND invitations.student_user_id IS NOT NULL
                AND users.role = 'student'
                AND NOT EXISTS (
                    SELECT 1
                    FROM athletes
                    WHERE athletes.user_id = users.id
                )
            """
        )

        connection.commit()

        print()
        print("ATLETAS SINCRONIZADOS")
        print("-" * 80)

        rows = cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                user_id,
                coach_user_id
            FROM athletes
            ORDER BY id
            """
        ).fetchall()

        for row in rows:
            print(
                row,
            )

        print()
        print(
            f"Total de atletas: {len(rows)}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()