"""add coach permissions and photo data

Revision ID: d3f90c7a4e21
Revises: b421ce718d20
Create Date: 2026-07-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d3f90c7a4e21"
down_revision: str | None = "b421ce718d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "coach_profiles",
        "photo_url",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.add_column(
        "coach_profiles",
        sa.Column(
            "can_view_athletes",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "coach_profiles",
        sa.Column(
            "can_administer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("coach_profiles", "can_administer")
    op.drop_column("coach_profiles", "can_view_athletes")
    op.alter_column(
        "coach_profiles",
        "photo_url",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=False,
    )
