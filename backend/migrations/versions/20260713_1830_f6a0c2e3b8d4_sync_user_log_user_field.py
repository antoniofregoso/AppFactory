"""sync the user field used by user log list and kanban views

Revision ID: f6a0c2e3b8d4
Revises: e5f9b1d2a7c3
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "f6a0c2e3b8d4"
down_revision = "e5f9b1d2a7c3"
branch_labels = None
depends_on = None


USER_FIELD = {
    "name": "user_id",
    "type": "many2one_avatar",
    "model": "user.user",
    "label": {"es_MX": "Usuario", "en_US": "User"},
    "list": {"column": 1},
    "kanban": {"header": "title"},
    "form": {
        "header": "title",
        "required": True,
        "readonly": True,
        "placeholder": {"es_MX": "Usuario", "en_US": "User"},
        "help": {
            "es_MX": "Usuario dueño de la sesión",
            "en_US": "User this session belongs to",
        },
    },
}

LIST_COLUMNS = {
    "user_id": 1,
    "status": 2,
    "start_date": 3,
    "last_seen_at": 4,
    "end_date": 5,
    "duration": 6,
}


def _set_field_metadata() -> None:
    op.execute(
        """
        UPDATE system_model_fields AS field
        SET type = 'many2one_avatar', required = true, readonly = true
        FROM system_models AS model
        WHERE field.model_id = model.id
          AND model.name = 'user.log'
          AND field.name = 'user_id'
        """
    )


def _set_view(user_kanban_header: str) -> None:
    connection = op.get_bind()
    schemas = connection.execute(
        sa.text(
            """
            SELECT schema.id, schema.view
            FROM system_model_schemas AS schema
            JOIN system_models AS model ON model.id = schema.model_id
            WHERE model.name = 'user.log'
              AND jsonb_typeof(schema.view) = 'array'
            """
        )
    ).mappings()

    for schema in schemas:
        view = schema["view"]
        user_field = {**USER_FIELD, "kanban": {"header": user_kanban_header}}
        replaced = False
        for index, field in enumerate(view):
            if field.get("name") in {"name", "user_id"}:
                view[index] = user_field
                replaced = True
                continue
            column = LIST_COLUMNS.get(field.get("name"))
            if column is not None:
                field["list"] = {**field.get("list", {}), "column": column}
        if not replaced:
            view.insert(1, user_field)
        connection.execute(
            sa.text(
                "UPDATE system_model_schemas SET view = CAST(:view AS jsonb) WHERE id = :id"
            ),
            {"id": schema["id"], "view": json.dumps(view)},
        )


def upgrade():
    _set_field_metadata()
    _set_view("title")


def downgrade():
    _set_view("subtitle")
