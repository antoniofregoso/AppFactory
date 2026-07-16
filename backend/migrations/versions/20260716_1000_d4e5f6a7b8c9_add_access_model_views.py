"""add access model views

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-16 10:00:00
"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _access_data(file_name: str) -> list[dict]:
    path = (
        Path(__file__).resolve().parents[2]
        / "app/domains/access/data"
        / file_name
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _upsert_model(connection, record: dict) -> int:
    values = {
        "name": record["name"],
        "label": json.dumps(record.get("label", {})),
        "group_by": record.get("group_by") or None,
        "group_by_values": json.dumps(record.get("group_by_values") or []),
        "tags": json.dumps(record.get("tags") or []),
    }
    model_id = connection.execute(
        sa.text("SELECT id FROM system_models WHERE name = :name ORDER BY id LIMIT 1"),
        {"name": record["name"]},
    ).scalar_one_or_none()
    if model_id is None:
        model_id = connection.execute(
            sa.text("""
                INSERT INTO system_models (
                    name, search, readonly, label, group_by, group_by_values, tags
                ) VALUES (
                    :name, false, false, CAST(:label AS jsonb), :group_by,
                    CAST(:group_by_values AS jsonb), CAST(:tags AS jsonb)
                )
                RETURNING id
            """),
            values,
        ).scalar_one()
    else:
        connection.execute(
            sa.text("""
                UPDATE system_models
                SET label = CAST(:label AS jsonb),
                    group_by = :group_by,
                    group_by_values = CAST(:group_by_values AS jsonb),
                    tags = CAST(:tags AS jsonb)
                WHERE id = :model_id
            """),
            {**values, "model_id": model_id},
        )
    return model_id


def _upsert_fields(connection, model_id: int, fields: list[dict]) -> None:
    for index, field in enumerate(fields, start=1):
        search_config = {}
        if field.get("selection_values"):
            search_config["selection_values"] = field["selection_values"]
        values = {
            "model_id": model_id,
            "name": field["name"],
            "sequence": field.get("sequence", index * 10),
            "type": field.get("type", "string"),
            "required": field.get("required", False),
            "readonly": field.get("readonly", False),
            "placeholder": json.dumps(field.get("placeholder") or {}),
            "help": json.dumps(field.get("help") or {}),
            "search_config": json.dumps(search_config),
        }
        field_id = connection.execute(
            sa.text("""
                SELECT id FROM system_model_fields
                WHERE model_id = :model_id AND name = :name
                ORDER BY id LIMIT 1
            """),
            values,
        ).scalar_one_or_none()
        if field_id is None:
            connection.execute(
                sa.text("""
                    INSERT INTO system_model_fields (
                        model_id, name, sequence, type, required, readonly,
                        placeholder, help, search_config
                    ) VALUES (
                        :model_id, :name, :sequence, :type, :required, :readonly,
                        CAST(:placeholder AS jsonb), CAST(:help AS jsonb),
                        CAST(:search_config AS jsonb)
                    )
                """),
                values,
            )
        else:
            connection.execute(
                sa.text("""
                    UPDATE system_model_fields
                    SET sequence = :sequence, type = :type, required = :required,
                        readonly = :readonly, placeholder = CAST(:placeholder AS jsonb),
                        help = CAST(:help AS jsonb),
                        search_config = CAST(:search_config AS jsonb)
                    WHERE id = :field_id
                """),
                {**values, "field_id": field_id},
            )


def _upsert_schema(connection, model_id: int, record: dict) -> None:
    values = {
        "model_id": model_id,
        "name": record["name"],
        "use": record["use"],
        "view": json.dumps(record.get("view") or []),
    }
    schema_id = connection.execute(
        sa.text("""
            SELECT id FROM system_model_schemas
            WHERE model_id = :model_id AND name = :name AND use = :use
            ORDER BY id LIMIT 1
        """),
        values,
    ).scalar_one_or_none()
    if schema_id is None:
        connection.execute(
            sa.text("""
                INSERT INTO system_model_schemas (model_id, name, use, view)
                VALUES (:model_id, :name, :use, CAST(:view AS jsonb))
            """),
            values,
        )
    else:
        connection.execute(
            sa.text("""
                UPDATE system_model_schemas
                SET view = CAST(:view AS jsonb)
                WHERE id = :schema_id
            """),
            {**values, "schema_id": schema_id},
        )


def upgrade() -> None:
    connection = op.get_bind()
    models = _access_data("system_model.json")
    schemas = _access_data("system_model_schema.json")
    model_ids = {}
    for model in models:
        model_id = _upsert_model(connection, model)
        model_ids[model["name"]] = model_id
        _upsert_fields(connection, model_id, model.get("fields", []))
    for schema in schemas:
        _upsert_schema(connection, model_ids[schema["model"]], schema)


def downgrade() -> None:
    connection = op.get_bind()
    names = tuple(record["name"] for record in _access_data("system_model.json"))
    connection.execute(
        sa.text("""
            DELETE FROM system_model_schemas
            WHERE model_id IN (SELECT id FROM system_models WHERE name IN :names)
        """).bindparams(sa.bindparam("names", expanding=True)),
        {"names": names},
    )
    connection.execute(
        sa.text("""
            DELETE FROM system_model_fields
            WHERE model_id IN (SELECT id FROM system_models WHERE name IN :names)
        """).bindparams(sa.bindparam("names", expanding=True)),
        {"names": names},
    )
    connection.execute(
        sa.text("DELETE FROM system_models WHERE name IN :names").bindparams(
            sa.bindparam("names", expanding=True)
        ),
        {"names": names},
    )
