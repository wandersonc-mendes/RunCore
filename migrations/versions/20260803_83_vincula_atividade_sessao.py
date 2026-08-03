# Vincula atividade importada à sessão planejada.
# Revision ID: 20260803_83_activity_link
# Revises: 20260803_81_activity_metrics

from alembic import op
import sqlalchemy as sa


revision = "20260803_83_activity_link"
down_revision = "20260803_81_activity_metrics"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "imported_activities",
        sa.Column(
            "training_session_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_imported_activities_training_session",
        "imported_activities",
        "training_sessions",
        ["training_session_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "uq_imported_activities_training_session_id",
        "imported_activities",
        ["training_session_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "uq_imported_activities_training_session_id",
        table_name="imported_activities",
    )

    op.drop_constraint(
        "fk_imported_activities_training_session",
        "imported_activities",
        type_="foreignkey",
    )

    op.drop_column(
        "imported_activities",
        "training_session_id",
    )
