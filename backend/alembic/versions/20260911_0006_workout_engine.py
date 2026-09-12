"""Create local workout execution engine tables."""

import sqlalchemy as sa
from alembic import op

revision = "20260911_0006"
down_revision = "20260911_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "local_workouts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("import_id", sa.String(64), nullable=True),
        sa.Column("hevy_workout_id", sa.String(64), nullable=True),
        sa.Column("hevy_routine_id", sa.String(64), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_local_workouts_import_id", "local_workouts", ["import_id"])
    op.create_index("ix_local_workouts_hevy_workout_id", "local_workouts", ["hevy_workout_id"])
    op.create_index("ix_local_workouts_hevy_routine_id", "local_workouts", ["hevy_routine_id"])
    op.create_index("ix_local_workouts_name", "local_workouts", ["name"])
    op.create_index("ix_local_workouts_date", "local_workouts", ["date"])
    op.create_index("ix_local_workouts_status", "local_workouts", ["status"])
    op.create_table(
        "workout_exercises",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("workout_id", sa.String(36), nullable=False),
        sa.Column("exercise_id", sa.String(36), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("planned_sets", sa.Integer(), nullable=False),
        sa.Column("planned_reps", sa.Integer(), nullable=True),
        sa.Column("planned_load", sa.String(64), nullable=True),
        sa.Column("planned_time_seconds", sa.Integer(), nullable=True),
        sa.Column("planned_distance_meters", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workout_id"], ["local_workouts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_id", "sequence_index", name="uq_workout_exercise_sequence"),
    )
    op.create_index("ix_workout_exercises_workout_id", "workout_exercises", ["workout_id"])
    op.create_index("ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"])
    op.create_table(
        "workout_set_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("workout_exercise_id", sa.String(36), nullable=False),
        sa.Column("set_index", sa.Integer(), nullable=False),
        sa.Column("actual_reps", sa.Integer(), nullable=True),
        sa.Column("actual_load", sa.String(64), nullable=True),
        sa.Column("actual_time_seconds", sa.Integer(), nullable=True),
        sa.Column("actual_distance_meters", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workout_exercise_id"], ["workout_exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_exercise_id", "set_index", name="uq_workout_set_log_index"),
    )
    op.create_index("ix_workout_set_logs_workout_exercise_id", "workout_set_logs", ["workout_exercise_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_set_logs_workout_exercise_id", table_name="workout_set_logs")
    op.drop_table("workout_set_logs")
    op.drop_index("ix_workout_exercises_exercise_id", table_name="workout_exercises")
    op.drop_index("ix_workout_exercises_workout_id", table_name="workout_exercises")
    op.drop_table("workout_exercises")
    for name in ("ix_local_workouts_status", "ix_local_workouts_date", "ix_local_workouts_name", "ix_local_workouts_hevy_routine_id", "ix_local_workouts_hevy_workout_id", "ix_local_workouts_import_id"):
        op.drop_index(name, table_name="local_workouts")
    op.drop_table("local_workouts")