"""add generic role based access control and remove is_admin

Revision ID: 9fa0b1c2d3e4
Revises: 8e9f0a1b2c3d
Create Date: 2026-07-15 15:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9fa0b1c2d3e4"
down_revision: Union[str, None] = "8e9f0a1b2c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("create_by", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "access_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()"), unique=True),
        sa.Column("code", sa.String(160), nullable=False, unique=True),
        sa.Column("domain", sa.String(80), nullable=False),
        sa.Column("resource", sa.String(80), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("name", postgresql.JSONB(), nullable=False),
        sa.Column("description", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        *_audit_columns(),
    )
    op.create_index("ix_access_permissions_uuid", "access_permissions", ["uuid"])
    op.create_index("ix_access_permissions_code", "access_permissions", ["code"])
    op.create_index("ix_access_permissions_domain", "access_permissions", ["domain"])
    op.create_table(
        "access_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()"), unique=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("system_companies.id"), nullable=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", postgresql.JSONB(), nullable=False),
        sa.Column("description", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("company_id", "code", name="uq_access_role_company_code"),
    )
    op.create_index("ix_access_roles_uuid", "access_roles", ["uuid"])
    op.create_index("ix_access_roles_company_id", "access_roles", ["company_id"])
    op.create_index("ix_access_roles_code", "access_roles", ["code"])
    op.create_table(
        "access_role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("access_roles.id"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("access_permissions.id"), primary_key=True),
    )
    op.create_table(
        "access_user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()"), unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_user.id"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("access_roles.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("system_companies.id"), nullable=True),
        sa.Column("scope_type", sa.String(8), nullable=False),
        sa.Column("scope_model", sa.String(160), nullable=True),
        sa.Column("scope_record_uuid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date_start", sa.Date(), nullable=True),
        sa.Column("date_end", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        *_audit_columns(),
    )
    for column in ("uuid", "user_id", "role_id", "company_id", "scope_type", "scope_model", "scope_record_uuid"):
        op.create_index(f"ix_access_user_roles_{column}", "access_user_roles", [column])
    # Preserve every existing administrator before removing the legacy flag.
    op.execute(sa.text("""
        INSERT INTO access_permissions
            (code, domain, resource, action, name, description, active, created_at)
        VALUES
            ('*', '*', '*', '*',
             '{"es_MX":"Acceso total","en_US":"Full access"}'::jsonb,
             '{"es_MX":"Administración global de la plataforma"}'::jsonb,
             true, CURRENT_TIMESTAMP)
    """))
    op.execute(sa.text("""
        INSERT INTO access_roles
            (code, name, description, active, sequence, created_at)
        VALUES
            ('platform_admin',
             '{"es_MX":"Administrador de plataforma","en_US":"Platform administrator"}'::jsonb,
             '{"es_MX":"Control global para configuración y soporte"}'::jsonb,
             true, 1, CURRENT_TIMESTAMP)
    """))
    op.execute(sa.text("""
        INSERT INTO access_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM access_roles r, access_permissions p
        WHERE r.code = 'platform_admin' AND r.company_id IS NULL AND p.code = '*'
    """))
    op.execute(sa.text("""
        INSERT INTO access_user_roles
            (user_id, role_id, scope_type, active, created_at)
        SELECT u.id, r.id, 'GLOBAL', true, CURRENT_TIMESTAMP
        FROM user_user u
        CROSS JOIN access_roles r
        WHERE u.is_admin = true
          AND r.code = 'platform_admin'
          AND r.company_id IS NULL
    """))
    op.drop_column("user_user", "is_admin")


def downgrade() -> None:
    op.add_column("user_user", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.drop_table("access_user_roles")
    op.drop_table("access_role_permissions")
    op.drop_table("access_roles")
    op.drop_table("access_permissions")
