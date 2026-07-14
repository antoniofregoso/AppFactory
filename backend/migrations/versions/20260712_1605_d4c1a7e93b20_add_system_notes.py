"""add system notes

Revision ID: d4c1a7e93b20
Revises: 4f70a29461a8
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4c1a7e93b20"
down_revision = "4f70a29461a8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_notes",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("create_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("record_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["system_companies.id"]),
        sa.ForeignKeyConstraint(["create_by"], ["user_user.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["system_models.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["user_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_system_notes_uuid", "system_notes", ["uuid"])
    op.create_index("ix_system_notes_record", "system_notes", ["company_id", "model_id", "record_uuid"])


def downgrade():
    op.drop_index("ix_system_notes_record", table_name="system_notes")
    op.drop_index("ix_system_notes_uuid", table_name="system_notes")
    op.drop_table("system_notes")
