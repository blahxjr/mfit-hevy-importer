"""Preserve cached Hevy routine exercise plans locally."""

import sqlalchemy as sa
from alembic import op

revision = "20260911_0007"
down_revision = "20260911_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("routines", sa.Column("exercise_plan", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("routines", "exercise_plan")