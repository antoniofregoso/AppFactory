"""add readonly system models

Revision ID: a7b1d3f4c9e5
Revises: f6a0c2e3b8d4
"""

import sqlalchemy as sa
from alembic import op


revision = "a7b1d3f4c9e5"
down_revision = "f6a0c2e3b8d4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "system_models",
        sa.Column("readonly", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE system_models SET readonly = true WHERE name = 'user.log'")


def downgrade():
    op.drop_column("system_models", "readonly")
