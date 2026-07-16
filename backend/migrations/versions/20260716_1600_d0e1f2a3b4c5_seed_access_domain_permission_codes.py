"""seed access domain permission codes

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-07-16 16:00:00
"""

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None

_NEW_CODES = {
    "access.permission.read",
    "access.permission.create",
    "access.permission.update",
    "access.permission.delete",
    "access.role.read",
    "access.role.create",
    "access.role.update",
    "access.role.delete",
    "access.user.role.read",
    "access.user.role.create",
    "access.user.role.update",
    "access.user.role.delete",
}


def _access_control_records() -> list[dict]:
    path = Path(__file__).resolve().parents[2] / "app/domains/access/data/access_control.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    return [record for record in source.get("permissions") or [] if record["code"] in _NEW_CODES]


def _permission_parts(code: str) -> tuple[str, str, str]:
    parts = code.split(".")
    if code == "*":
        return "*", "*", "*"
    if code.endswith(".*"):
        return parts[0], ".".join(parts[1:-1]) or "*", "*"
    return parts[0], ".".join(parts[1:-1]), parts[-1]


def upgrade() -> None:
    connection = op.get_bind()
    for record in _access_control_records():
        domain, resource, action = _permission_parts(record["code"])
        connection.execute(
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
        )


def downgrade() -> None:
    connection = op.get_bind()
    code_filter = sa.bindparam("codes", expanding=True)
    connection.execute(
        sa.text("""
            DELETE FROM access_role_permissions
            WHERE permission_id IN (
                SELECT id FROM access_permissions WHERE code IN :codes
            )
        """).bindparams(code_filter),
        {"codes": tuple(_NEW_CODES)},
    )
    connection.execute(
        sa.text("DELETE FROM access_permissions WHERE code IN :codes").bindparams(code_filter),
        {"codes": tuple(_NEW_CODES)},
    )
