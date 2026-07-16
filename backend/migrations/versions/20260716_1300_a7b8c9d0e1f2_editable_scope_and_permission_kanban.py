"""make scope model editable and simplify permission kanban

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-16 13:00:00
"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
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
    models = {item["name"]: item for item in _access_data("system_model.json")}
    scope_model = next(
        field for field in models["access.user.role"]["fields"]
        if field["name"] == "scope_model"
    )
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = :type,
                required = :required,
                readonly = :readonly,
                placeholder = CAST(:placeholder AS jsonb),
                help = CAST(:help AS jsonb)
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'access.user.role'
              AND field.name = 'scope_model'
        """),
        {
            "type": scope_model["type"],
            "required": scope_model.get("required", False),
            "readonly": scope_model.get("readonly", False),
            "placeholder": json.dumps(scope_model.get("placeholder") or {}),
            "help": json.dumps(scope_model.get("help") or {}),
        },
    )

    schemas = _access_data("system_model_schema.json")
    for model_name in ("access.permission", "access.user.role"):
        schema = next(
            item for item in schemas
            if item["model"] == model_name
            and item["name"] == "default"
            and item["use"] == "view"
        )
        connection.execute(
            sa.text("""
                UPDATE system_model_schemas AS schema
                SET view = CAST(:view AS jsonb)
                FROM system_models AS model
                WHERE schema.model_id = model.id
                  AND model.name = :model_name
                  AND schema.name = 'default'
                  AND schema.use = 'view'
            """),
            {"model_name": model_name, "view": json.dumps(schema["view"])},
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET readonly = true
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'access.user.role'
              AND field.name = 'scope_model'
        """)
    )
