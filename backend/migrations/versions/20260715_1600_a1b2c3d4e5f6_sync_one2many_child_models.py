"""sync one2many child models

Revision ID: a1b2c3d4e5f6
Revises: 9fa0b1c2d3e4
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "9fa0b1c2d3e4"
branch_labels = None
depends_on = None


CHILD_MODELS = {
    ("parties.party", "employees"): "parties.party",
    ("system.company", "users"): "user.user",
}


def _schemas(connection):
    return connection.execute(
        sa.text("""
            SELECT schema.id, model.name AS model, schema.view
            FROM system_model_schemas AS schema
            JOIN system_models AS model ON model.id = schema.model_id
            WHERE schema.use = 'view'
              AND model.name IN ('parties.party', 'system.company')
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
    for schema in _schemas(connection):
        changed = False
        view = list(schema["view"] or [])
        for field in view:
            child_model = CHILD_MODELS.get((schema["model"], field.get("name")))
            if child_model and field.get("model") != child_model:
                field["model"] = child_model
                changed = True
        if changed:
            _write_view(connection, schema["id"], view)


def downgrade():
    connection = op.get_bind()
    for schema in _schemas(connection):
        changed = False
        view = list(schema["view"] or [])
        for field in view:
            if (schema["model"], field.get("name")) in CHILD_MODELS and "model" in field:
                field.pop("model")
                changed = True
        if changed:
            _write_view(connection, schema["id"], view)
