"""add system push subscriptions

Revision ID: c7a1f3e9b2d4
Revises: b3d6e2f4a891
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c7a1f3e9b2d4"
down_revision = "b3d6e2f4a891"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("create_by", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=True),
        sa.UniqueConstraint("endpoint", name="uq_system_push_subscriptions_endpoint"),
    )
    op.create_index(
        "ix_system_push_subscriptions_uuid",
        "system_push_subscriptions",
        ["uuid"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_system_push_subscriptions_uuid", table_name="system_push_subscriptions")
    op.drop_table("system_push_subscriptions")
