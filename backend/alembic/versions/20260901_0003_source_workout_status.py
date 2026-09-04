"""Add granular approval status to source workouts."""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0003"
down_revision = "20260901_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "source_workouts",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
    )


def downgrade() -> None:
    op.drop_column("source_workouts", "status")
