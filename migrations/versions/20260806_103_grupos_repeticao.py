"""Adiciona grupos de repetição aos blocos de treino.

Revision ID: 20260806_103_repeat_groups
Revises: 20260803_95_multicriteria
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260806_103_repeat_groups"
down_revision = "20260803_95_multicriteria"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "training_steps",
        sa.Column("group_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "training_steps",
        sa.Column("group_order", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_steps",
        sa.Column(
            "group_repetitions",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.create_check_constraint(
        "ck_training_steps_group_repetitions",
        "training_steps",
        "group_repetitions BETWEEN 1 AND 100",
    )
    op.create_check_constraint(
        "ck_training_steps_group_consistency",
        "training_steps",
        (
            "(group_id IS NULL AND group_order IS NULL) OR "
            "(group_id IS NOT NULL AND group_order IS NOT NULL)"
        ),
    )


def downgrade():
    op.drop_constraint(
        "ck_training_steps_group_consistency",
        "training_steps",
        type_="check",
    )
    op.drop_constraint(
        "ck_training_steps_group_repetitions",
        "training_steps",
        type_="check",
    )
    op.drop_column("training_steps", "group_repetitions")
    op.drop_column("training_steps", "group_order")
    op.drop_column("training_steps", "group_id")
