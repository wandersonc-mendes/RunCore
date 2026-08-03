# Separa objetivo e orientações da sessão.
# Revision ID: 20260802_78_session_objective
# Revises: d3f90c7a4e21

from alembic import op
import sqlalchemy as sa


revision = "20260802_78_session_objective"
down_revision = "d3f90c7a4e21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "training_sessions",
        sa.Column(
            "objective",
            sa.String(length=1000),
            nullable=False,
            server_default="",
        ),
    )

    op.execute(
        "UPDATE training_sessions "
        "SET objective = COALESCE(notes, ''), "
        "notes = ''"
    )


def downgrade():
    op.execute(
        "UPDATE training_sessions "
        "SET notes = CASE "
        "WHEN COALESCE(notes, '') = '' "
        "THEN COALESCE(objective, '') "
        "ELSE notes END"
    )

    op.drop_column(
        "training_sessions",
        "objective",
    )
