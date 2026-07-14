"""add privacy-preserving search audits

Revision ID: c9d3f5a6e1b7
Revises: b8c2e4f5d0a6
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c9d3f5a6e1b7"
down_revision = "b8c2e4f5d0a6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_search_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "models",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("query_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "error_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index(
        op.f("ix_system_search_audits_created_at"),
        "system_search_audits",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_system_search_audits_query_hash"),
        "system_search_audits",
        ["query_hash"],
    )
    op.create_index(
        op.f("ix_system_search_audits_request_id"),
        "system_search_audits",
        ["request_id"],
    )
    op.create_index(
        op.f("ix_system_search_audits_status"),
        "system_search_audits",
        ["status"],
    )
    op.create_index(
        op.f("ix_system_search_audits_user_id"),
        "system_search_audits",
        ["user_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_system_search_audits_user_id"),
        table_name="system_search_audits",
    )
    op.drop_index(
        op.f("ix_system_search_audits_status"),
        table_name="system_search_audits",
    )
    op.drop_index(
        op.f("ix_system_search_audits_request_id"),
        table_name="system_search_audits",
    )
    op.drop_index(
        op.f("ix_system_search_audits_query_hash"),
        table_name="system_search_audits",
    )
    op.drop_index(
        op.f("ix_system_search_audits_created_at"),
        table_name="system_search_audits",
    )
    op.drop_table("system_search_audits")
