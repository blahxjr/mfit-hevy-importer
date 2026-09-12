"""Create local exercise catalog."""

import sqlalchemy as sa
from alembic import op

revision = "20260911_0005"
down_revision = "20260910_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("exercises",
        sa.Column("id", sa.String(36), nullable=False), sa.Column("exercisedb_id", sa.String(128)),
        sa.Column("hevy_template_id", sa.String(64)), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255)), sa.Column("body_part", sa.String(128)), sa.Column("target_muscle", sa.String(128)),
        sa.Column("secondary_muscles", sa.Text()), sa.Column("equipment", sa.String(128)), sa.Column("movement_pattern", sa.String(64)),
        sa.Column("instructions", sa.Text()), sa.Column("image_url", sa.String(2048)), sa.Column("video_url", sa.String(2048)),
        sa.Column("media_hint", sa.String(32)), sa.Column("source", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hevy_template_id"], ["exercise_templates.id"]), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exercisedb_id", name="uq_exercises_exercisedb_id"))
    for name, column in (("ix_exercises_exercisedb_id", "exercisedb_id"), ("ix_exercises_name", "name"), ("ix_exercises_name_en", "name_en"), ("ix_exercises_movement_pattern", "movement_pattern"), ("ix_exercises_source", "source"), ("ix_exercises_hevy_template_id", "hevy_template_id")):
        op.create_index(name, "exercises", [column])


def downgrade() -> None:
    for name in ("ix_exercises_hevy_template_id", "ix_exercises_source", "ix_exercises_movement_pattern", "ix_exercises_name_en", "ix_exercises_name", "ix_exercises_exercisedb_id"):
        op.drop_index(name, table_name="exercises")
    op.drop_table("exercises")