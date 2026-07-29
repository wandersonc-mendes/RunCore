"""add coach profiles

Revision ID: b421ce718d20
Revises: 6a81c36f42d0
Create Date: 2026-07-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b421ce718d20"
down_revision: str | None = "6a81c36f42d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coach_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("cpf", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("rg", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("team_role", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("cref", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("instagram", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("show_public_profile", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("photo_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("zip_code", sa.String(length=12), nullable=False, server_default=""),
        sa.Column("address", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("address_number", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("address_extra", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("neighborhood", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("city", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("state", sa.String(length=2), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("phone_secondary", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("curriculum", sa.Text(), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("coach_profiles")
