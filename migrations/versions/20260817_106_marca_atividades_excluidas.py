"""Adiciona exclusão reversível às atividades importadas.

Revision ID: 20260817_106_deleted_activities
Revises: 20260817_105_strava_wancorre
"""

import sqlalchemy as sa
from alembic import op


revision = "20260817_106_deleted_activities"
down_revision = "20260817_105_strava_wancorre"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "imported_activities",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("imported_activities", "deleted_at")
