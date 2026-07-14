"""add declarative search metadata

Revision ID: a1f4b9c2d7e0
Revises: 8c25f91d6a44
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a1f4b9c2d7e0"
down_revision = "8c25f91d6a44"
branch_labels = None
depends_on = None


def _models():
    path = Path(__file__).resolve().parents[2] / "app/domains/system/data/system_models.json"
    return json.loads(path.read_text(encoding="utf-8"))


def upgrade():
    op.add_column("system_models", sa.Column("search", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "system_model_fields",
        sa.Column("search_config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    connection = op.get_bind()
    for model in _models():
        if model.get("search"):
            connection.execute(sa.text("UPDATE system_models SET search = true WHERE name = :name"), {"name": model["name"]})
        for field in model.get("fields", []):
            if field.get("search"):
                connection.execute(
                    sa.text("""
                        UPDATE system_model_fields AS field
                        SET search_config = CAST(:config AS jsonb)
                        FROM system_models AS model
                        WHERE field.model_id = model.id AND model.name = :model AND field.name = :field
                    """),
                    {"config": json.dumps(field["search"]), "model": model["name"], "field": field["name"]},
                )


def downgrade():
    op.drop_column("system_model_fields", "search_config")
    op.drop_column("system_models", "search")
