"""Initial migration: all persistence tables.

Revision ID: 20260901_0001
Revises:
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exercise_templates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=True),
        sa.Column("primary_muscle_group", sa.String(length=64), nullable=True),
        sa.Column("secondary_muscle_groups", sa.Text(), nullable=True),
        sa.Column("equipment", sa.String(length=64), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exercise_templates_title", "exercise_templates", ["title"])
    op.create_table(
        "routine_folders",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
    )
    op.create_index("ix_routine_folders_title", "routine_folders", ["title"])
    op.create_table(
        "imports",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
    )
    op.create_index("ix_imports_sha256", "imports", ["sha256"])
    op.create_table(
        "routines",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["folder_id"], ["routine_folders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routines_title", "routines", ["title"])
    op.create_table(
        "exercise_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("template_id", sa.String(length=64), nullable=True),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["exercise_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_name", name="uq_exercise_mapping_source"),
    )
    op.create_index("ix_exercise_mappings_source_name", "exercise_mappings", ["source_name"])
    op.create_table(
        "source_workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_id", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_id", sa.String(length=64), nullable=False),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("agent_version", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=True),
        sa.Column("output_hash", sa.String(length=64), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_exercises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("sets_raw", sa.String(length=255), nullable=True),
        sa.Column("reps_raw", sa.String(length=255), nullable=True),
        sa.Column("load_raw", sa.String(length=255), nullable=True),
        sa.Column("rest_raw", sa.String(length=255), nullable=True),
        sa.Column("notes_raw", sa.Text(), nullable=True),
        sa.Column("techniques", sa.Text(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("source_location", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["workout_id"], ["source_workouts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("source_exercises")
    op.drop_table("audit_events")
    op.drop_table("source_workouts")
    op.drop_index("ix_exercise_mappings_source_name", table_name="exercise_mappings")
    op.drop_table("exercise_mappings")
    op.drop_index("ix_routines_title", table_name="routines")
    op.drop_table("routines")
    op.drop_index("ix_imports_sha256", table_name="imports")
    op.drop_table("imports")
    op.drop_index("ix_routine_folders_title", table_name="routine_folders")
    op.drop_table("routine_folders")
    op.drop_index("ix_exercise_templates_title", table_name="exercise_templates")
    op.drop_table("exercise_templates")
