"""seed modular access control declarations

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-16 15:00:00
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def _sources() -> list[dict]:
    domains = Path(__file__).resolve().parents[2] / "app/domains"
    return [
        json.loads((domains / domain / "data/access_control.json").read_text(encoding="utf-8"))
        for domain in ("access", "talent", "parties")
    ]


def _permission_parts(code: str) -> tuple[str, str, str]:
    parts = code.split(".")
    if code == "*":
        return "*", "*", "*"
    if code.endswith(".*"):
        return parts[0], ".".join(parts[1:-1]) or "*", "*"
    return parts[0], ".".join(parts[1:-1]), parts[-1]


def upgrade() -> None:
    connection = op.get_bind()
    sources = _sources()
    permission_ids = {}
    for source in sources:
        for record in source.get("permissions") or []:
            domain, resource, action = _permission_parts(record["code"])
            permission_id = connection.execute(
                sa.text("""
                    INSERT INTO access_permissions (
                        code, domain, resource, action, name, description,
                        active, created_at
                    ) VALUES (
                        :code, :domain, :resource, :action,
                        CAST(:name AS jsonb), CAST(:description AS jsonb),
                        :active, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (code) DO UPDATE SET
                        domain = EXCLUDED.domain,
                        resource = EXCLUDED.resource,
                        action = EXCLUDED.action,
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        active = EXCLUDED.active
                    RETURNING id
                """),
                {
                    "code": record["code"],
                    "domain": domain,
                    "resource": resource,
                    "action": action,
                    "name": json.dumps(record.get("name") or {}),
                    "description": json.dumps(record.get("description") or {}),
                    "active": record.get("active", True),
                },
            ).scalar_one()
            permission_ids[record["code"]] = permission_id

    role_ids = {}
    role_records = []
    for source in sources:
        for record in source.get("roles") or []:
            role_id = connection.execute(
                sa.text("""
                    SELECT id FROM access_roles
                    WHERE code = :code AND company_id IS NULL
                    ORDER BY id LIMIT 1
                """),
                {"code": record["code"]},
            ).scalar_one_or_none()
            values = {
                "code": record["code"],
                "name": json.dumps(record.get("name") or {}),
                "description": json.dumps(record.get("description") or {}),
                "active": record.get("active", True),
                "sequence": record.get("sequence", 10),
            }
            if role_id is None:
                role_id = connection.execute(
                    sa.text("""
                        INSERT INTO access_roles (
                            code, name, description, active, sequence, created_at
                        ) VALUES (
                            :code, CAST(:name AS jsonb), CAST(:description AS jsonb),
                            :active, :sequence, CURRENT_TIMESTAMP
                        )
                        RETURNING id
                    """),
                    values,
                ).scalar_one()
            else:
                connection.execute(
                    sa.text("""
                        UPDATE access_roles
                        SET name = CAST(:name AS jsonb),
                            description = CAST(:description AS jsonb),
                            active = :active,
                            sequence = :sequence
                        WHERE id = :role_id
                    """),
                    {**values, "role_id": role_id},
                )
            role_ids[record["code"]] = role_id
            role_records.append((role_id, record))

    for role_id, record in role_records:
        connection.execute(
            sa.text("DELETE FROM access_role_permissions WHERE role_id = :role_id"),
            {"role_id": role_id},
        )
        for permission_code in record.get("permissions") or []:
            connection.execute(
                sa.text("""
                    INSERT INTO access_role_permissions (role_id, permission_id)
                    VALUES (:role_id, :permission_id)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                """),
                {
                    "role_id": role_id,
                    "permission_id": permission_ids[permission_code],
                },
            )

    for source in sources:
        for record in source.get("assignments") or []:
            connection.execute(
                sa.text("""
                    INSERT INTO access_user_roles (
                        user_id, role_id, company_id, scope_type, scope_model,
                        scope_record_uuid, active, created_at
                    )
                    SELECT
                        user_record.id,
                        :role_id,
                        CASE WHEN :scope_type = 'GLOBAL' THEN NULL ELSE user_record.company_id END,
                        CAST(:scope_type AS accessscopetype),
                        :scope_model,
                        CAST(:scope_record_uuid AS uuid),
                        :active,
                        CURRENT_TIMESTAMP
                    FROM user_user AS user_record
                    WHERE user_record.email = :user_email
                      AND NOT EXISTS (
                          SELECT 1 FROM access_user_roles AS assignment
                          WHERE assignment.user_id = user_record.id
                            AND assignment.role_id = :role_id
                            AND assignment.scope_type::text = :scope_type
                      )
                """),
                {
                    "user_email": record["user_email"],
                    "role_id": role_ids[record["role"]],
                    "scope_type": record.get("scope_type", "COMPANY"),
                    "scope_model": record.get("scope_model"),
                    "scope_record_uuid": record.get("scope_record_uuid"),
                    "active": record.get("active", True),
                },
            )


def downgrade() -> None:
    connection = op.get_bind()
    sources = _sources()
    role_codes = tuple(
        record["code"]
        for source in sources
        for record in source.get("roles") or []
        if record["code"] != "platform_admin"
    )
    permission_codes = tuple(
        record["code"]
        for source in sources
        for record in source.get("permissions") or []
        if record["code"] != "*"
    )
    role_filter = sa.bindparam("role_codes", expanding=True)
    permission_filter = sa.bindparam("permission_codes", expanding=True)
    connection.execute(
        sa.text("""
            DELETE FROM access_user_roles
            WHERE role_id IN (SELECT id FROM access_roles WHERE code IN :role_codes)
        """).bindparams(role_filter),
        {"role_codes": role_codes},
    )
    connection.execute(
        sa.text("""
            DELETE FROM access_role_permissions
            WHERE role_id IN (SELECT id FROM access_roles WHERE code IN :role_codes)
        """).bindparams(role_filter),
        {"role_codes": role_codes},
    )
    connection.execute(
        sa.text("DELETE FROM access_roles WHERE code IN :role_codes").bindparams(role_filter),
        {"role_codes": role_codes},
    )
    connection.execute(
        sa.text("DELETE FROM access_permissions WHERE code IN :permission_codes").bindparams(permission_filter),
        {"permission_codes": permission_codes},
    )
