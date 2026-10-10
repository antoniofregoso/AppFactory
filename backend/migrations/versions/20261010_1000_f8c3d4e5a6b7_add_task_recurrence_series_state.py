"""add task recurrence series state

Revision ID: f8c3d4e5a6b7
Revises: e7b2c3d4e5f6
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f8c3d4e5a6b7"
down_revision = "e7b2c3d4e5f6"
branch_labels = None
depends_on = None


def _has_column(connection, name: str) -> bool:
    return any(
        column["name"] == name
        for column in sa.inspect(connection).get_columns("system_tasks")
    )


def upgrade():
    connection = op.get_bind()
    if not _has_column(connection, "recurrence_until"):
        op.add_column(
            "system_tasks",
            sa.Column("recurrence_until", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column(connection, "recurrence_exceptions"):
        op.add_column(
            "system_tasks",
            sa.Column(
                "recurrence_exceptions",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
        )


def downgrade():
    connection = op.get_bind()
    if _has_column(connection, "recurrence_exceptions"):
        op.drop_column("system_tasks", "recurrence_exceptions")
    if _has_column(connection, "recurrence_until"):
        op.drop_column("system_tasks", "recurrence_until")
