"""add the virtual insight model

Revision ID: f2a6c8d9b4e0
Revises: e1f5b7c8a3d9
"""

import sqlalchemy as sa
from alembic import op

revision = "f2a6c8d9b4e0"
down_revision = "e1f5b7c8a3d9"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO system_models
            (
                uuid,
                name,
                search,
                readonly,
                label,
                group_by_values,
                tags,
                created_at
            )
        SELECT
            gen_random_uuid(),
            'system.insight',
            false,
            true,
            '{"es_MX":"Paneles de información","en_US":"Insights"}'::jsonb,
            '[]'::jsonb,
            '[]'::jsonb,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (
            SELECT 1 FROM system_models WHERE name = 'system.insight'
        )
        """))
    connection.execute(sa.text("""
        UPDATE system_model_schemas AS schema
        SET model_id = insight.id
        FROM system_models AS insight
        WHERE insight.name = 'system.insight'
          AND schema.name = 'userLogs'
          AND schema.use = 'insight'
        """))


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE system_model_schemas AS schema
        SET model_id = user_log.id
        FROM system_models AS user_log
        WHERE user_log.name = 'user.log'
          AND schema.name = 'userLogs'
          AND schema.use = 'insight'
        """))
    connection.execute(sa.text("""
        DELETE FROM system_models
        WHERE name = 'system.insight'
          AND NOT EXISTS (
              SELECT 1
              FROM system_model_schemas
              WHERE model_id = system_models.id
          )
        """))
