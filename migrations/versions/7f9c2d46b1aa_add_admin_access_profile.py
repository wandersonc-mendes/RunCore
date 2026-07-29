"""add administrative access profile

Revision ID: 7f9c2d46b1aa
Revises: 815c3babe3fe
Create Date: 2026-07-29
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "7f9c2d46b1aa"
down_revision: str | Sequence[str] | None = "815c3babe3fe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("role", sa.String),
        sa.column("is_active", sa.Boolean),
    )

    first_coach_id = connection.execute(
        sa.select(users.c.id)
        .where(
            users.c.role == "coach",
            users.c.is_active.is_(True),
        )
        .order_by(users.c.id)
        .limit(1),
    ).scalar()

    if first_coach_id is not None:
        connection.execute(
            users.update()
            .where(users.c.id == first_coach_id)
            .values(role="admin"),
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE users SET role = 'coach' WHERE role = 'admin'",
        ),
    )
