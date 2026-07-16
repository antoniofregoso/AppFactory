"""ungroup permission kanban

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-16 14:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            UPDATE system_models
            SET group_by = NULL, group_by_values = '[]'::jsonb
            WHERE name = 'access.permission'
        """)
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            UPDATE system_models
            SET group_by = 'domain'
            WHERE name = 'access.permission'
        """)
    )
