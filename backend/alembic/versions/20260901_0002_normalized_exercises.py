"""Add normalized exercises."""
import sqlalchemy as sa

from alembic import op

revision = "20260901_0002"
down_revision = "20260901_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "normalized_exercises",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_exercise_id", sa.Integer, sa.ForeignKey("source_exercises.id"), nullable=False, unique=True),
        sa.Column("sets_min", sa.Integer),
        sa.Column("sets_max", sa.Integer),
        sa.Column("reps_min", sa.Integer),
        sa.Column("reps_max", sa.Integer),
        sa.Column("load_value", sa.Float),
        sa.Column("load_unit", sa.String(8)),
        sa.Column("rest_seconds", sa.Integer),
        sa.Column("is_timed", sa.Boolean, nullable=False),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("sets_raw", sa.String(255)),
        sa.Column("reps_raw", sa.String(255)),
        sa.Column("load_raw", sa.String(255)),
        sa.Column("rest_raw", sa.String(255)),
        sa.Column("needs_review", sa.Boolean, nullable=False),
        sa.Column("review_reason", sa.Text),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_normalized_exercises_source_exercise_id", "normalized_exercises", ["source_exercise_id"])


def downgrade():
    op.drop_table("normalized_exercises")
