"""add persisted user sessions

Revision ID: d0e4a6b7f2c8
Revises: c9d3f5a6e1b7
"""

import sqlalchemy as sa
from alembic import op

revision = "d0e4a6b7f2c8"
down_revision = "c9d3f5a6e1b7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "uuid",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "absolute_expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(
        op.f("ix_user_sessions_refresh_token_hash"),
        "user_sessions",
        ["refresh_token_hash"],
    )
    op.create_index(
        op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"]
    )
    op.create_index(op.f("ix_user_sessions_uuid"), "user_sessions", ["uuid"])


def downgrade():
    op.drop_index(op.f("ix_user_sessions_uuid"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(
        op.f("ix_user_sessions_refresh_token_hash"),
        table_name="user_sessions",
    )
    op.drop_table("user_sessions")
