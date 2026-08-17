"""Mantém ativa somente a integração Strava do WanCorre.

Revision ID: 20260817_105_strava_wancorre
Revises: 20260813_104_manual_sessions
"""

from alembic import op
from sqlalchemy import text


revision = "20260817_105_strava_wancorre"
down_revision = "20260813_104_manual_sessions"
branch_labels = None
depends_on = None


TARGET_NAME = "wancorre"


def upgrade():
    connection = op.get_bind()
    user_ids = connection.execute(
        text(
            """
            SELECT DISTINCT candidate.user_id
            FROM (
                SELECT users.id AS user_id
                FROM users
                WHERE lower(trim(users.name)) = :target_name

                UNION

                SELECT athletes.user_id
                FROM athletes
                WHERE athletes.user_id IS NOT NULL
                  AND lower(trim(athletes.name)) = :target_name
            ) AS candidate
            ORDER BY candidate.user_id
            """
        ),
        {"target_name": TARGET_NAME},
    ).scalars().all()

    if len(user_ids) != 1:
        raise RuntimeError(
            "Limpeza Strava abortada: WanCorre deve corresponder "
            f"a exatamente um usuário; encontrados={len(user_ids)}."
        )

    keep_user_id = user_ids[0]
    has_strava = connection.execute(
        text(
            """
            SELECT 1
            FROM external_integrations
            WHERE provider = 'strava'
              AND user_id = :keep_user_id
            LIMIT 1
            """
        ),
        {"keep_user_id": keep_user_id},
    ).scalar_one_or_none()

    if has_strava is None:
        raise RuntimeError(
            "Limpeza Strava abortada: WanCorre não possui integração Strava."
        )

    result = connection.execute(
        text(
            """
            UPDATE external_integrations
            SET active = false
            WHERE provider = 'strava'
              AND user_id <> :keep_user_id
              AND active = true
            """
        ),
        {"keep_user_id": keep_user_id},
    )

    print(
        "STRAVA_CONNECTIONS_CLEANUP "
        f"keep_user_id={keep_user_id} "
        f"deactivated={result.rowcount}",
        flush=True,
    )


def downgrade():
    # Os estados anteriores não podem ser reconstruídos com segurança.
    pass
