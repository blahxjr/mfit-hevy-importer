"""Add per-workout exercise reference media."""

import sqlalchemy as sa
from alembic import op

revision = "20260910_0006"
down_revision = "20260909_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workout_exercise_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_id", sa.String(length=64), nullable=False),
        sa.Column("exercise_index", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("local_file_name", sa.String(length=255), nullable=True),
        sa.Column("alt_text", sa.String(length=255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["exercise_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("import_id", "exercise_index", name="uq_workout_exercise_media_import_index"),
        sa.CheckConstraint(
            "(source = 'placeholder') OR (image_url IS NOT NULL OR local_file_name IS NOT NULL)",
            name="ck_workout_exercise_media_has_media",
        ),
    )


def downgrade() -> None:
    op.drop_table("workout_exercise_media")
