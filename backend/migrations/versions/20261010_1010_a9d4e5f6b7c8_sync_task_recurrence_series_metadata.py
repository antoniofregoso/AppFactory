"""sync task recurrence series metadata

Revision ID: a9d4e5f6b7c8
Revises: f8c3d4e5a6b7
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "a9d4e5f6b7c8"
down_revision = "f8c3d4e5a6b7"
branch_labels = None
depends_on = None

RECURRENCE_SCHEMA_FIELD = {
    "name": "recurrence",
    "type": "string",
    "label": {"es_MX": "Recurrencia", "en_US": "Recurrence"},
    "list": {"column": 6},
    "kanban": {"footer": 1},
}
SERIES_SCHEMA_FIELDS = [
    {
        "name": "recurrence_until",
        "type": "datetime",
        "hidden": True,
        "label": {"es_MX": "Fin de recurrencia", "en_US": "Recurrence end"},
    },
    {
        "name": "recurrence_exceptions",
        "type": "json",
        "hidden": True,
        "label": {
            "es_MX": "Excepciones de recurrencia",
            "en_US": "Recurrence exceptions",
        },
    },
]
SERIES_MODEL_FIELDS = [
    {
        "name": "recurrence_until",
        "type": "datetime",
        "help": {
            "es_MX": "Última fecha incluida en la serie",
            "en_US": "Last date included in the series",
        },
    },
    {
        "name": "recurrence_exceptions",
        "type": "json",
        "help": {
            "es_MX": "Ocurrencias excluidas de la serie",
            "en_US": "Occurrences excluded from the series",
        },
    },
]


def _upsert_field(connection, field: dict) -> None:
    values = {
        "name": field["name"],
        "type": field["type"],
        "help": json.dumps(field["help"]),
    }
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = :type, required = FALSE, readonly = TRUE,
                placeholder = '{}'::jsonb, help = CAST(:help AS jsonb)
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'system.task'
              AND field.name = :name
            """),
        values,
    )
    connection.execute(
        sa.text("""
            INSERT INTO system_model_fields (
                name, sequence, type, required, readonly,
                placeholder, help, search_config, model_id
            )
            SELECT :name, 10, :type, FALSE, TRUE,
                   '{}'::jsonb, CAST(:help AS jsonb), '{}'::jsonb, model.id
            FROM system_models AS model
            WHERE model.name = 'system.task'
              AND NOT EXISTS (
                  SELECT 1 FROM system_model_fields AS field
                  WHERE field.model_id = model.id AND field.name = :name
              )
            """),
        values,
    )


def upgrade():
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE system_model_fields AS field
        SET required = FALSE
        FROM system_models AS model
        WHERE field.model_id = model.id
          AND model.name = 'system.task'
          AND field.name = 'description'
        """))
    for field in SERIES_MODEL_FIELDS:
        _upsert_field(connection, field)
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = (
                SELECT COALESCE(jsonb_agg(
                    CASE
                        WHEN item->>'name' = 'description'
                        THEN jsonb_set(item, '{form,required}', 'false'::jsonb, TRUE)
                        WHEN item->>'name' = 'recurrence'
                        THEN CAST(:recurrence AS jsonb)
                        ELSE item
                    END ORDER BY position
                ), '[]'::jsonb)
                || CASE WHEN EXISTS (
                    SELECT 1 FROM jsonb_array_elements(schema.view) AS current_item
                    WHERE current_item->>'name' = 'recurrence'
                ) THEN '[]'::jsonb ELSE jsonb_build_array(CAST(:recurrence AS jsonb)) END
                || CAST(:series_fields AS jsonb)
                FROM jsonb_array_elements(schema.view) WITH ORDINALITY AS source(item, position)
                WHERE item->>'name' NOT IN ('recurrence_until', 'recurrence_exceptions')
            )
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'system.task'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """),
        {
            "recurrence": json.dumps(RECURRENCE_SCHEMA_FIELD),
            "series_fields": json.dumps(SERIES_SCHEMA_FIELDS),
        },
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("""
        DELETE FROM system_model_fields AS field
        USING system_models AS model
        WHERE field.model_id = model.id
          AND model.name = 'system.task'
          AND field.name IN ('recurrence_until', 'recurrence_exceptions')
        """))
    connection.execute(sa.text("""
        UPDATE system_model_fields AS field
        SET required = TRUE
        FROM system_models AS model
        WHERE field.model_id = model.id
          AND model.name = 'system.task'
          AND field.name = 'description'
        """))
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = (
                SELECT COALESCE(jsonb_agg(
                    CASE
                        WHEN item->>'name' = 'description'
                        THEN jsonb_set(item, '{form,required}', 'true'::jsonb, TRUE)
                        WHEN item->>'name' = 'recurrence'
                        THEN CAST(:recurrence AS jsonb)
                        ELSE item
                    END ORDER BY position
                ), '[]'::jsonb)
                FROM jsonb_array_elements(schema.view) WITH ORDINALITY AS source(item, position)
                WHERE item->>'name' NOT IN ('recurrence_until', 'recurrence_exceptions')
            )
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'system.task'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """),
        {
            "recurrence": json.dumps({
                "name": "recurrence",
                "type": "string",
                "label": {"es_MX": "Recurrencia", "en_US": "Recurrence"},
            })
        },
    )
