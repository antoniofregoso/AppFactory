"""add talent domain

Revision ID: 7d8e9f0a1b2c
Revises: 6ac7d12e843f
Create Date: 2026-07-15 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7d8e9f0a1b2c"
down_revision: Union[str, None] = "6ac7d12e843f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns():
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("create_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["create_by"], ["user_user.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["user_user.id"]),
    )


def _identity_columns():
    return (
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "uuid",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )


def upgrade() -> None:
    op.create_table(
        "talent_systems",
        *_audit_columns(),
        *_identity_columns(),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "description", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["system_companies.id"]),
        sa.UniqueConstraint(
            "company_id", "code", name="uq_talent_system_company_code"
        ),
    )
    op.create_index("ix_talent_systems_uuid", "talent_systems", ["uuid"])
    op.create_index(
        "ix_talent_systems_company_id", "talent_systems", ["company_id"]
    )
    op.create_index("ix_talent_systems_code", "talent_systems", ["code"])

    op.create_table(
        "talent_areas",
        *_audit_columns(),
        *_identity_columns(),
        sa.Column("system_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "description", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["talent_systems.id"]),
        sa.UniqueConstraint("system_id", "code", name="uq_talent_area_system_code"),
    )
    op.create_index("ix_talent_areas_uuid", "talent_areas", ["uuid"])
    op.create_index("ix_talent_areas_system_id", "talent_areas", ["system_id"])
    op.create_index("ix_talent_areas_code", "talent_areas", ["code"])

    op.create_table(
        "talent_positions",
        *_audit_columns(),
        *_identity_columns(),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("parent_position_id", sa.Integer(), nullable=True),
        sa.Column("name", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mission", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["talent_areas.id"]),
        sa.ForeignKeyConstraint(
            ["parent_position_id"], ["talent_positions.id"]
        ),
        sa.UniqueConstraint("area_id", "code", name="uq_talent_position_area_code"),
    )
    op.create_index("ix_talent_positions_uuid", "talent_positions", ["uuid"])
    op.create_index("ix_talent_positions_area_id", "talent_positions", ["area_id"])
    op.create_index("ix_talent_positions_code", "talent_positions", ["code"])
    op.create_index(
        "ix_talent_positions_parent_position_id",
        "talent_positions",
        ["parent_position_id"],
    )

    op.create_table(
        "talent_agents",
        *_audit_columns(),
        *_identity_columns(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("date_start", sa.Date(), nullable=True),
        sa.Column("date_end", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "date_end IS NULL OR date_start IS NULL OR date_end >= date_start",
            name="ck_talent_agent_dates",
        ),
        sa.ForeignKeyConstraint(["party_id"], ["parties_party.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["system_companies.id"]),
        sa.ForeignKeyConstraint(["position_id"], ["talent_positions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_user.id"]),
        sa.UniqueConstraint(
            "company_id", "party_id", name="uq_talent_agent_company_party"
        ),
    )
    op.create_index("ix_talent_agents_uuid", "talent_agents", ["uuid"])
    op.create_index("ix_talent_agents_party_id", "talent_agents", ["party_id"])
    op.create_index("ix_talent_agents_company_id", "talent_agents", ["company_id"])
    op.create_index("ix_talent_agents_position_id", "talent_agents", ["position_id"])
    op.create_index("ix_talent_agents_user_id", "talent_agents", ["user_id"])


def downgrade() -> None:
    op.drop_table("talent_agents")
    op.drop_table("talent_positions")
    op.drop_table("talent_areas")
    op.drop_table("talent_systems")
