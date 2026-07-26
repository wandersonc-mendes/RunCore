"""add ipt tables

Revision ID: 815c3babe3fe
Revises: 9c757f911275
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "815c3babe3fe"
down_revision: str | None = "9c757f911275"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ipt_protocols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("protocol_type", sa.String(length=20), nullable=False),
        sa.Column("short_value", sa.Float(), nullable=False),
        sa.Column("long_value", sa.Float(), nullable=False),
        sa.Column("input_mode", sa.String(length=20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "ipt_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("athlete_id", sa.Integer(), nullable=False),
        sa.Column("protocol_id", sa.Integer(), nullable=False),
        sa.Column("short_result", sa.Float(), nullable=False),
        sa.Column("long_result", sa.Float(), nullable=False),
        sa.Column("short_speed", sa.Float(), nullable=False),
        sa.Column("long_speed", sa.Float(), nullable=False),
        sa.Column("ipt_percentage", sa.Float(), nullable=False),
        sa.Column("profile", sa.String(length=20), nullable=False),
        sa.Column("interpretation", sa.String(length=500), nullable=False),
        sa.Column("emphasis", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"]),
        sa.ForeignKeyConstraint(["protocol_id"], ["ipt_protocols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ipt_assessments_athlete_id",
        "ipt_assessments",
        ["athlete_id"],
        unique=False,
    )

    op.create_index(
        "ix_ipt_assessments_protocol_id",
        "ipt_assessments",
        ["protocol_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ipt_assessments_protocol_id",
        table_name="ipt_assessments",
    )

    op.drop_index(
        "ix_ipt_assessments_athlete_id",
        table_name="ipt_assessments",
    )

    op.drop_table("ipt_assessments")
    op.drop_table("ipt_protocols")