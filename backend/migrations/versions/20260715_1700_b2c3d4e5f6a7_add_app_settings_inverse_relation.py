"""add app settings inverse relation metadata

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


APP_SETTING_RELATION = {
    "name": "app_id",
    "type": "many2one",
    "model": "system.app",
    "required": True,
    "label": {
        "es_MX": "Aplicación",
        "en_US": "Application",
    },
}


def _schemas(connection):
    return connection.execute(
        sa.text("""
            SELECT schema.id, model.name AS model, schema.view
            FROM system_model_schemas AS schema
            JOIN system_models AS model ON model.id = schema.model_id
            WHERE schema.name = 'default'
              AND schema.use = 'view'
              AND model.name IN ('system.app', 'system.app.settings')
            """)
    ).mappings()


def _write_view(connection, schema_id: int, view: list[dict]) -> None:
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas
            SET view = CAST(:view AS jsonb)
            WHERE id = :id
            """),
        {"id": schema_id, "view": json.dumps(view)},
    )


def upgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            INSERT INTO system_model_fields (
                name, sequence, type, required, readonly,
                placeholder, help, search_config, model_id
            )
            SELECT
                'app_id', 10, 'many2one', TRUE, FALSE,
                CAST(:placeholder AS jsonb), CAST(:help AS jsonb), '{}'::jsonb, model.id
            FROM system_models AS model
            WHERE model.name = 'system.app.settings'
              AND NOT EXISTS (
                  SELECT 1 FROM system_model_fields AS field
                  WHERE field.model_id = model.id AND field.name = 'app_id'
              )
            """),
        {
            "placeholder": json.dumps(
                {"es_MX": "Aplicación", "en_US": "Application"}
            ),
            "help": json.dumps(
                {
                    "es_MX": "Aplicación propietaria de la configuración",
                    "en_US": "Application that owns this setting",
                }
            ),
        },
    )

    for schema in _schemas(connection):
        view = list(schema["view"] or [])
        if schema["model"] == "system.app":
            settings_field = next(
                (field for field in view if field.get("name") == "settings_ids"),
                None,
            )
            if settings_field is not None:
                settings_field["model"] = "system.app.settings"
                _write_view(connection, schema["id"], view)
        elif not any(field.get("name") == "app_id" for field in view):
            _write_view(connection, schema["id"], [APP_SETTING_RELATION, *view])


def downgrade():
    connection = op.get_bind()
    for schema in _schemas(connection):
        view = list(schema["view"] or [])
        if schema["model"] == "system.app":
            for field in view:
                if field.get("name") == "settings_ids":
                    field.pop("model", None)
        else:
            view = [field for field in view if field.get("name") != "app_id"]
        _write_view(connection, schema["id"], view)

    connection.execute(
        sa.text("""
            DELETE FROM system_model_fields AS field
            USING system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'system.app.settings'
              AND field.name = 'app_id'
            """)
    )
