"""synchronize access views

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-16 11:00:00
"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
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
    schemas = _access_data("system_model_schema.json")

    for model_name, field_name in (
        ("access.permission", "action"),
        ("access.role", "permissions"),
    ):
        field = next(
            item for item in models[model_name]["fields"]
            if item["name"] == field_name
        )
        search_config = {}
        if field.get("selection_values"):
            search_config["selection_values"] = field["selection_values"]
        connection.execute(
            sa.text("""
                UPDATE system_model_fields AS field
                SET type = :type,
                    required = :required,
                    readonly = :readonly,
                    placeholder = CAST(:placeholder AS jsonb),
                    help = CAST(:help AS jsonb),
                    search_config = CAST(:search_config AS jsonb)
                FROM system_models AS model
                WHERE field.model_id = model.id
                  AND model.name = :model_name
                  AND field.name = :field_name
            """),
            {
                "model_name": model_name,
                "field_name": field_name,
                "type": field["type"],
                "required": field.get("required", False),
                "readonly": field.get("readonly", False),
                "placeholder": json.dumps(field.get("placeholder") or {}),
                "help": json.dumps(field.get("help") or {}),
                "search_config": json.dumps(search_config),
            },
        )

    for schema in schemas:
        connection.execute(
            sa.text("""
                UPDATE system_model_schemas AS schema
                SET view = CAST(:view AS jsonb)
                FROM system_models AS model
                WHERE schema.model_id = model.id
                  AND model.name = :model_name
                  AND schema.name = :name
                  AND schema.use = :use
            """),
            {
                "model_name": schema["model"],
                "name": schema["name"],
                "use": schema["use"],
                "view": json.dumps(schema.get("view") or []),
            },
        )


def downgrade() -> None:
    # The previous metadata remains structurally valid; no destructive rollback
    # is needed for a declarative-view synchronization.
    pass
