"""update country relation views

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


FIELD_TYPES = {
    "states": "one2many_kanban",
    "timezones": "many2many_pills",
}


def _timezone_data() -> list[dict]:
    path = (
        Path(__file__).resolve().parents[2]
        / "app/domains/system/data/system_timezone.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _country_schema(connection):
    return connection.execute(
        sa.text("""
            SELECT schema.id, schema.view
            FROM system_model_schemas AS schema
            JOIN system_models AS model ON model.id = schema.model_id
            WHERE model.name = 'system.country'
              AND schema.name = 'default'
              AND schema.use = 'view'
            """)
    ).mappings().one_or_none()


def _write_view(connection, schema_id: int, view: list[dict]) -> None:
    connection.execute(
        sa.text("""
            UPDATE system_model_schemas
            SET view = CAST(:view AS jsonb)
            WHERE id = :id
            """),
        {"id": schema_id, "view": json.dumps(view)},
    )


def _seed_timezones(connection) -> None:
    records = _timezone_data()
    connection.execute(
        sa.text("""
            INSERT INTO system_timezones (name, code)
            VALUES (:name, :code)
            ON CONFLICT (code) DO NOTHING
        """),
        [
            {"name": record["name"], "code": record["code"]}
            for record in records
        ],
    )
    relations = [
        {"timezone_code": record["code"], "country_code": country_code}
        for record in records
        for country_code in record.get("country_codes", [])
    ]
    if relations:
        connection.execute(
            sa.text("""
                INSERT INTO system_country_timezone_rel (country_id, timezone_id)
                SELECT country.id, timezone.id
                FROM system_countries AS country
                JOIN system_timezones AS timezone
                  ON timezone.code = :timezone_code
                WHERE country.code = :country_code
                ON CONFLICT (country_id, timezone_id) DO NOTHING
                """),
            relations,
        )


def upgrade():
    connection = op.get_bind()
    _seed_timezones(connection)
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = CASE field.name
                WHEN 'states' THEN 'one2many_kanban'
                WHEN 'timezones' THEN 'many2many_pills'
            END
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'system.country'
              AND field.name IN ('states', 'timezones')
            """)
    )

    schema = _country_schema(connection)
    if schema is None:
        return
    view = list(schema["view"] or [])
    for field in view:
        if field.get("name") == "states":
            field.update(type="one2many_kanban", model="system.country.state")
            field.setdefault("form", {}).update(
                view="one2many_kanban",
                kanban_view={
                    "header": {
                        "title": "name",
                        "subtitle": "code",
                    }
                },
            )
        elif field.get("name") == "name":
            field.setdefault("list", {})["order"] = "asc"
        elif field.get("name") == "timezones":
            field.update(type="many2many_pills", model="system.timezone")
    _write_view(connection, schema["id"], view)


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE system_model_fields AS field
            SET type = CASE field.name
                WHEN 'states' THEN 'one2many_list'
                WHEN 'timezones' THEN 'many2many'
            END
            FROM system_models AS model
            WHERE field.model_id = model.id
              AND model.name = 'system.country'
              AND field.name IN ('states', 'timezones')
            """)
    )

    schema = _country_schema(connection)
    if schema is None:
        return
    view = list(schema["view"] or [])
    for field in view:
        if field.get("name") == "states":
            field["type"] = "one2many_list"
            field.pop("model", None)
            form = field.get("form", {})
            form.pop("view", None)
            form.pop("kanban_view", None)
        elif field.get("name") == "name":
            field.setdefault("list", {})["order"] = True
        elif field.get("name") == "timezones":
            field["type"] = "many2many"
            field.pop("model", None)
    _write_view(connection, schema["id"], view)
