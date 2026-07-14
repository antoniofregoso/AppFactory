"""configure structured search fields

Revision ID: b8c2e4f5d0a6
Revises: a7b1d3f4c9e5
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "b8c2e4f5d0a6"
down_revision = "a7b1d3f4c9e5"
branch_labels = None
depends_on = None


def _models():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/domains/system/data/system_models.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _update_search_config(connection, model: str, field: str, config: dict) -> None:
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET search_config = CAST(:config AS jsonb)
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = :model
              AND field.name = :field
            """),
        {"config": json.dumps(config), "model": model, "field": field},
    )


def upgrade():
    connection = op.get_bind()
    configured_models = {"system.task", "system.message", "user.user"}
    for model in _models():
        if model["name"] not in configured_models:
            continue
        for field in model.get("fields", []):
            if field.get("search"):
                search_config = dict(field["search"])
                if field.get("selection_values"):
                    search_config["selection_values"] = field["selection_values"]
                _update_search_config(
                    connection,
                    model["name"],
                    field["name"],
                    search_config,
                )


def downgrade():
    connection = op.get_bind()
    previous = {
        ("system.message", "subject"): {
            "enabled": True,
            "text": True,
            "result": "title",
            "weight": "A",
        },
        ("system.message", "status"): {
            "enabled": True,
            "text": True,
            "result": "subtitle",
            "weight": "B",
        },
        ("system.task", "title"): {
            "enabled": True,
            "text": True,
            "result": "title",
            "weight": "A",
        },
        ("system.task", "status"): {
            "enabled": True,
            "text": True,
            "result": "subtitle",
            "weight": "B",
        },
        ("system.task", "priority"): {
            "enabled": True,
            "text": True,
            "result": "subtitle",
            "weight": "B",
        },
    }
    structured_fields = {
        ("system.message", "subject"),
        ("system.message", "status"),
        ("system.message", "date"),
        ("system.message", "from_user_id"),
        ("system.message", "to_users"),
        ("system.task", "title"),
        ("system.task", "status"),
        ("system.task", "priority"),
        ("system.task", "date_assign"),
        ("system.task", "date_due"),
        ("system.task", "user_id"),
        ("user.user", "name"),
        ("user.user", "email"),
    }
    for model, field in structured_fields:
        _update_search_config(
            connection, model, field, previous.get((model, field), {})
        )
