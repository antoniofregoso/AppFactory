"""add the declarative user logs insight schema

Revision ID: e1f5b7c8a3d9
Revises: d0e4a6b7f2c8
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "e1f5b7c8a3d9"
down_revision = "d0e4a6b7f2c8"
branch_labels = None
depends_on = None

INSIGHT_VIEW = {
    "period": "today",
    "layout": {"graphics": 2},
    "kpis": [
        "kpiUsersOnline",
        "kpiUsersAverageSessionTime",
        "kpiUsersActiveUsers",
        "kpiRecurringUsers",
    ],
    "gauges": [],
    "graphics": ["graphicUsersPerHour", "graphicUsersMAU"],
}


def upgrade():
    connection = op.get_bind()
    parameters = {"view": json.dumps(INSIGHT_VIEW)}
    updated = connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = CAST(:view AS jsonb)
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'user.log'
              AND schema.name = 'userLogs'
              AND schema.use = 'insight'
            """),
        parameters,
    )
    if updated.rowcount:
        return

    connection.execute(
        sa.text("""
            INSERT INTO system_model_schemas
                (uuid, name, use, view, model_id, created_at)
            SELECT
                gen_random_uuid(),
                'userLogs',
                'insight',
                CAST(:view AS jsonb),
                model.id,
                CURRENT_TIMESTAMP
            FROM system_models AS model
            WHERE model.name = 'user.log'
            """),
        parameters,
    )


def downgrade():
    op.execute("""
        DELETE FROM system_model_schemas AS schema
        USING system_models AS model
        WHERE schema.model_id = model.id
          AND model.name = 'user.log'
          AND schema.name = 'userLogs'
          AND schema.use = 'insight'
        """)
