"""Adiciona prescrição multicritério aos blocos.

Revision ID: 20260803_95_multicriteria
Revises: 20260803_83_activity_link
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260803_95_multicriteria"
down_revision = "20260803_83_activity_link"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "training_steps",
        sa.Column(
            "prescription_type",
            sa.String(length=16),
            nullable=False,
            server_default="distance",
        ),
    )
    op.add_column(
        "training_steps",
        sa.Column(
            "intensity_type",
            sa.String(length=20),
            nullable=False,
            server_default="pace",
        ),
    )
    op.add_column(
        "training_steps",
        sa.Column("heart_rate_min", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_steps",
        sa.Column("heart_rate_max", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_steps",
        sa.Column("rpe_min", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_steps",
        sa.Column("rpe_max", sa.Integer(), nullable=True),
    )

    op.create_check_constraint(
        "ck_training_steps_prescription_type",
        "training_steps",
        "prescription_type IN ('distance', 'duration')",
    )
    op.create_check_constraint(
        "ck_training_steps_intensity_type",
        "training_steps",
        "intensity_type IN ('pace', 'heart_rate', 'rpe', 'free')",
    )
    op.create_check_constraint(
        "ck_training_steps_heart_rate_range",
        "training_steps",
        (
            "(heart_rate_min IS NULL OR heart_rate_min > 0) AND "
            "(heart_rate_max IS NULL OR heart_rate_max > 0) AND "
            "(heart_rate_min IS NULL OR heart_rate_max IS NULL "
            "OR heart_rate_min <= heart_rate_max)"
        ),
    )
    op.create_check_constraint(
        "ck_training_steps_rpe_range",
        "training_steps",
        (
            "(rpe_min IS NULL OR rpe_min BETWEEN 1 AND 10) AND "
            "(rpe_max IS NULL OR rpe_max BETWEEN 1 AND 10) AND "
            "(rpe_min IS NULL OR rpe_max IS NULL "
            "OR rpe_min <= rpe_max)"
        ),
    )


def downgrade():
    op.drop_constraint(
        "ck_training_steps_rpe_range",
        "training_steps",
        type_="check",
    )
    op.drop_constraint(
        "ck_training_steps_heart_rate_range",
        "training_steps",
        type_="check",
    )
    op.drop_constraint(
        "ck_training_steps_intensity_type",
        "training_steps",
        type_="check",
    )
    op.drop_constraint(
        "ck_training_steps_prescription_type",
        "training_steps",
        type_="check",
    )

    op.drop_column("training_steps", "rpe_max")
    op.drop_column("training_steps", "rpe_min")
    op.drop_column("training_steps", "heart_rate_max")
    op.drop_column("training_steps", "heart_rate_min")
    op.drop_column("training_steps", "intensity_type")
    op.drop_column("training_steps", "prescription_type")
