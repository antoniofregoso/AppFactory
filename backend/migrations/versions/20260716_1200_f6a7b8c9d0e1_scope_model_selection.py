"""configure access scope model selection

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-16 12:00:00
"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _access_data(file_name: str) -> list[dict]:
    path = (
        Path(__file__).resolve().parents[2]
        / "app/domains/access/data"
        / file_name
    )
    return json.loads(path.read_text(encoding="utf-8"))


def upgrade() -> None:
    connection = op.get_bind()
    model = next(
        item for item in _access_data("system_model.json")
        if item["name"] == "access.user.role"
    )
    field = next(item for item in model["fields"] if item["name"] == "scope_model")
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = :type,
                required = :required,
                readonly = :readonly,
                placeholder = CAST(:placeholder AS jsonb),
                help = CAST(:help AS jsonb),
                search_config = '{}'::jsonb
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'access.user.role'
              AND field.name = 'scope_model'
        """),
        {
            "type": field["type"],
            "required": field.get("required", False),
            "readonly": field.get("readonly", False),
            "placeholder": json.dumps(field.get("placeholder") or {}),
            "help": json.dumps(field.get("help") or {}),
        },
    )

    schema = next(
        item for item in _access_data("system_model_schema.json")
        if item["model"] == "access.user.role"
        and item["name"] == "default"
        and item["use"] == "view"
    )
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = CAST(:view AS jsonb)
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'access.user.role'
              AND schema.name = 'default'
              AND schema.use = 'view'
        """),
        {"view": json.dumps(schema["view"])},
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = 'string', readonly = false
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'access.user.role'
              AND field.name = 'scope_model'
        """)
    )
    row = connection.execute(
        sa.text("""
            SELECT schema.id, schema.view
            FROM system_model_schemas AS schema
            JOIN system_models AS model ON model.id = schema.model_id
            WHERE model.name = 'access.user.role'
              AND schema.name = 'default'
              AND schema.use = 'view'
        """)
    ).mappings().one_or_none()
    if row is None:
        return
    view = list(row["view"] or [])
    for item in view:
        if item.get("name") != "scope_model":
            continue
        item["type"] = "string"
        item.pop("selection_model", None)
        item.setdefault("form", {})["readonly"] = False
    connection.execute(
        sa.text("UPDATE system_model_schemas SET view = CAST(:view AS jsonb) WHERE id = :id"),
        {"id": row["id"], "view": json.dumps(view)},
    )
