"""add task recurrence

Revision ID: e7b2c3d4e5f6
Revises: d0e1f2a3b4c5
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "e7b2c3d4e5f6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None

RECURRENCE_SCHEMA_FIELD = {
    "name": "recurrence",
    "type": "string",
    "label": {"es_MX": "Recurrencia", "en_US": "Recurrence"},
}


def upgrade():
    op.add_column(
        "system_tasks",
        sa.Column("recurrence", sa.String(length=255), nullable=True),
    )
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            INSERT INTO system_model_fields (
                name, sequence, type, required, readonly,
                placeholder, help, search_config, model_id
            )
            SELECT
                'recurrence', 10, 'string', FALSE, FALSE,
                CAST(:placeholder AS jsonb), CAST(:help AS jsonb), '{}'::jsonb, model.id
            FROM system_models AS model
            WHERE model.name = 'system.task'
              AND NOT EXISTS (
                  SELECT 1 FROM system_model_fields AS field
                  WHERE field.model_id = model.id AND field.name = 'recurrence'
              )
            """),
        {
            "placeholder": json.dumps({"es_MX": "Recurrencia", "en_US": "Recurrence"}),
            "help": json.dumps(
                {
                    "es_MX": "Regla de repetición de la tarea",
                    "en_US": "Rule used to repeat the task",
                }
            ),
        },
    )
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = schema.view || CAST(:field AS jsonb)
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'system.task'
              AND schema.name = 'default'
              AND schema.use = 'view'
              AND NOT EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(schema.view) AS item
                  WHERE item->>'name' = 'recurrence'
              )
            """),
        {"field": json.dumps([RECURRENCE_SCHEMA_FIELD])},
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = (
                SELECT COALESCE(jsonb_agg(item), '[]'::jsonb)
                FROM jsonb_array_elements(schema.view) AS item
                WHERE item->>'name' <> 'recurrence'
            )
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'system.task'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """)
    )
    connection.execute(
        sa.text("""
            DELETE FROM system_model_fields AS field
            USING system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'system.task'
              AND field.name = 'recurrence'
            """)
    )
    op.drop_column("system_tasks", "recurrence")
