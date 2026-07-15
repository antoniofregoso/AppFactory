"""add multilingual position to parties

Revision ID: 8e9f0a1b2c3d
Revises: 7d8e9f0a1b2c
Create Date: 2026-07-15 13:00:00
"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8e9f0a1b2c3d"
down_revision: Union[str, None] = "7d8e9f0a1b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _party_data(file_name: str):
    path = (
        Path(__file__).resolve().parents[2]
        / "app/domains/parties/data"
        / file_name
    )
    return json.loads(path.read_text(encoding="utf-8"))


def upgrade() -> None:
    op.add_column(
        "parties_party",
        sa.Column(
            "position",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    connection = op.get_bind()
    model_definition = next(
        item for item in _party_data("system_models.json")
        if item["name"] == "parties.party"
    )
    position_index, position = next(
        (index, field)
        for index, field in enumerate(model_definition["fields"], start=1)
        if field["name"] == "position"
    )
    connection.execute(
        sa.text("""
            INSERT INTO system_model_fields (
                name, sequence, type, required, readonly,
                placeholder, help, search_config, model_id
            )
            SELECT
                :name, :sequence, :type, :required, :readonly,
                CAST(:placeholder AS jsonb), CAST(:help AS jsonb), '{}'::jsonb, model.id
            FROM system_models AS model
            WHERE model.name = 'parties.party'
              AND NOT EXISTS (
                  SELECT 1 FROM system_model_fields AS field
                  WHERE field.model_id = model.id AND field.name = :name
              )
            """),
        {
            "name": position["name"],
            "sequence": position.get("sequence", position_index * 10),
            "type": position["type"],
            "required": position.get("required", False),
            "readonly": position.get("readonly", False),
            "placeholder": json.dumps(position.get("placeholder", {})),
            "help": json.dumps(position.get("help", {})),
        },
    )
    schema = next(
        item for item in _party_data("system_model_schemas.json")
        if item["model"] == "parties.party"
        and item["name"] == "default"
        and item["use"] == "view"
    )
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = CAST(:view AS jsonb)
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'parties.party'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """),
        {"view": json.dumps(schema["view"])},
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            DELETE FROM system_model_fields AS field
            USING system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'parties.party'
              AND field.name = 'position'
            """)
    )
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas AS schema
            SET view = (
                SELECT COALESCE(jsonb_agg(item), '[]'::jsonb)
                FROM jsonb_array_elements(schema.view) AS item
                WHERE item->>'name' <> 'position'
            )
            FROM system_models AS model
            WHERE schema.model_id = model.id
              AND model.name = 'parties.party'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """)
    )
    op.drop_column("parties_party", "position")
