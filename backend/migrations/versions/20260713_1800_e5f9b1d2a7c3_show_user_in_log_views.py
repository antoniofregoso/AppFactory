"""show the user name in user log views

Revision ID: e5f9b1d2a7c3
Revises: d4e8a0c1f6b2
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "e5f9b1d2a7c3"
down_revision = "d4e8a0c1f6b2"
branch_labels = None
depends_on = None


def _user_field(name: str, field_type: str, *, include_list: bool) -> dict:
    field = {
        "name": name,
        "type": field_type,
        "label": {"es_MX": "Usuario", "en_US": "User"},
        "kanban": {"header": "subtitle"},
        "form": {
            "header": "subtitle",
            "required": True,
            "readonly": True,
            "placeholder": {"es_MX": "Usuario", "en_US": "User"},
            "help": {
                "es_MX": "Usuario dueño de la sesión",
                "en_US": "User this session belongs to",
            },
        },
    }
    if field_type == "many2one_avatar":
        field["model"] = "user.user"
    if include_list:
        field["list"] = {"column": 1}
    return field


def _update_view(*, user_field: dict, shift: int) -> None:
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
        for index, field in enumerate(view):
            if field.get("name") in {"name", "user_id"}:
                view[index] = user_field
                continue
            list_config = field.get("list")
            if list_config and isinstance(list_config.get("column"), int):
                list_config["column"] += shift
        connection.execute(
            sa.text(
                "UPDATE system_model_schemas SET view = CAST(:view AS jsonb) WHERE id = :id"
            ),
            {"id": schema["id"], "view": json.dumps(view)},
        )


def upgrade():
    _update_view(
        user_field=_user_field("user_id", "many2one_avatar", include_list=True),
        shift=1,
    )


def downgrade():
    _update_view(
        user_field=_user_field("name", "string", include_list=False),
        shift=-1,
    )
