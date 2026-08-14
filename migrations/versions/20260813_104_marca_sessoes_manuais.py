"""Marca sessões de treino alteradas manualmente.

Revision ID: 20260813_104_manual_sessions
Revises: 20260806_103_repeat_groups
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_104_manual_sessions"
down_revision = "20260806_103_repeat_groups"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "training_sessions",
        sa.Column(
            "manual_override",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column(
        "training_sessions",
        "manual_override",
    )
