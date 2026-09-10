"""Create exercise template media support."""

import sqlalchemy as sa

from alembic import op

revision = "20260909_0005"
down_revision = "20260908_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exercise_template_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("local_file_name", sa.String(length=255), nullable=True),
        sa.Column("alt_text", sa.String(length=255), nullable=False),
        sa.Column("attribution", sa.String(length=255), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["exercise_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", name="uq_exercise_template_media_template_id"),
        sa.CheckConstraint(
            "(source = 'placeholder') OR (image_url IS NOT NULL OR local_file_name IS NOT NULL)",
            name="ck_exercise_template_media_has_media",
        ),
    )


def downgrade() -> None:
    op.drop_table("exercise_template_media")
