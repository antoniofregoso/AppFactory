"""add is_admin and mcp_access to user_user

Revision ID: d4e8a0c1f6b2
Revises: c7a1f3e9b2d4
"""

import sqlalchemy as sa
from alembic import op

revision = "d4e8a0c1f6b2"
down_revision = "c7a1f3e9b2d4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_user",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_user",
        sa.Column("mcp_access", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("user_user", "mcp_access")
    op.drop_column("user_user", "is_admin")
