"""add notification priority and dedupe key

Revision ID: b3d6e2f4a891
Revises: a1f4b9c2d7e0
"""

import sqlalchemy as sa
from alembic import op

revision = "b3d6e2f4a891"
down_revision = "a1f4b9c2d7e0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "system_notifications",
        sa.Column("priority", sa.String(32), nullable=False, server_default="info"),
    )
    op.add_column(
        "system_notifications",
        sa.Column("dedupe_key", sa.String(255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_system_notifications_dedupe_key", "system_notifications", ["dedupe_key"]
    )


def downgrade():
    op.drop_constraint(
        "uq_system_notifications_dedupe_key", "system_notifications", type_="unique"
    )
    op.drop_column("system_notifications", "dedupe_key")
    op.drop_column("system_notifications", "priority")
