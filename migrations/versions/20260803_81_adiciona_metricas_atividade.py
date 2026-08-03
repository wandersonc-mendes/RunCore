# Adiciona métricas fisiológicas e mecânicas.
# Revision ID: 20260803_81_activity_metrics
# Revises: 20260802_78_session_objective

from alembic import op
import sqlalchemy as sa


revision = "20260803_81_activity_metrics"
down_revision = "20260802_78_session_objective"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "imported_activities",
        sa.Column(
            "elapsed_time",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "average_speed",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "max_speed",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "average_heartrate",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "max_heartrate",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "average_cadence",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "max_cadence",
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        "imported_activities",
        sa.Column(
            "total_elevation_gain",
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "imported_activities",
        "total_elevation_gain",
    )
    op.drop_column(
        "imported_activities",
        "max_cadence",
    )
    op.drop_column(
        "imported_activities",
        "average_cadence",
    )
    op.drop_column(
        "imported_activities",
        "max_heartrate",
    )
    op.drop_column(
        "imported_activities",
        "average_heartrate",
    )
    op.drop_column(
        "imported_activities",
        "max_speed",
    )
    op.drop_column(
        "imported_activities",
        "average_speed",
    )
    op.drop_column(
        "imported_activities",
        "elapsed_time",
    )
