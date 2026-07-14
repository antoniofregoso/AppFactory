"""configure html search fields

Revision ID: 24d8babba860
Revises: 86c64ea5062c
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "24d8babba860"
down_revision = "86c64ea5062c"
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
    html_search_fields = {("system.task", "description"), ("system.message", "message")}
    for model in _models():
        for field in model.get("fields", []):
            key = (model["name"], field["name"])
            if key in html_search_fields and field.get("search"):
                _update_search_config(connection, *key, dict(field["search"]))


def downgrade():
    connection = op.get_bind()
    for model, field in (("system.task", "description"), ("system.message", "message")):
        _update_search_config(connection, model, field, {})
