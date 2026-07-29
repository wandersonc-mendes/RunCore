"""promote primary administrator to master

Revision ID: 6a81c36f42d0
Revises: 7f9c2d46b1aa
Create Date: 2026-07-29
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "6a81c36f42d0"
down_revision: str | Sequence[str] | None = "7f9c2d46b1aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    users = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("role", sa.String),
    )

    connection.execute(
        users.update()
        .where(
            sa.func.lower(users.c.email)
            == "wandersoncmendes@gmail.com",
        )
        .values(role="master"),
    )


def downgrade() -> None:
    connection = op.get_bind()
    users = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("role", sa.String),
    )

    connection.execute(
        users.update()
        .where(
            sa.func.lower(users.c.email)
            == "wandersoncmendes@gmail.com",
            users.c.role == "master",
        )
        .values(role="admin"),
    )
