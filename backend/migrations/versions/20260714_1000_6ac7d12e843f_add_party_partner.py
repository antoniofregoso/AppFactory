"""add parent partner relation to parties

Revision ID: 6ac7d12e843f
Revises: 5fb991178534
"""

import sqlalchemy as sa
from alembic import op

revision = "6ac7d12e843f"
down_revision = "5fb991178534"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "parties_party",
        sa.Column("partner_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_parties_party_partner_id_parties_party",
        "parties_party",
        "parties_party",
        ["partner_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_parties_party_partner_id"),
        "parties_party",
        ["partner_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_parties_party_partner_id"),
        table_name="parties_party",
    )
    op.drop_constraint(
        "fk_parties_party_partner_id_parties_party",
        "parties_party",
        type_="foreignkey",
    )
    op.drop_column("parties_party", "partner_id")
