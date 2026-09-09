"""Create exercise canonicalization persistence."""

import sqlalchemy as sa

from alembic import op

revision = "20260908_0004"
down_revision = "20260901_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exercise_canonicalizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_exercise_id", sa.Integer(), nullable=False),
        sa.Column("source_name_pt", sa.String(length=255), nullable=False),
        sa.Column("canonical_name_en", sa.String(length=255), nullable=True),
        sa.Column("search_aliases_en", sa.Text(), nullable=True),
        sa.Column("movement_pattern", sa.String(length=64), nullable=True),
        sa.Column("equipment_hint", sa.String(length=64), nullable=True),
        sa.Column("primary_muscle_hint", sa.String(length=128), nullable=True),
        sa.Column("secondary_muscles_hint", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("raw_response_sanitized", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_exercise_id"], ["source_exercises.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_exercise_id",
            name="uq_exercise_canonicalizations_source_exercise_id",
        ),
    )
    op.create_index(
        "ix_exercise_canonicalizations_canonical_name_en",
        "exercise_canonicalizations",
        ["canonical_name_en"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_exercise_canonicalizations_canonical_name_en",
        table_name="exercise_canonicalizations",
    )
    op.drop_table("exercise_canonicalizations")
