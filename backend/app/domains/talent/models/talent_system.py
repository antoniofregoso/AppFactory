import uuid
from typing import List, Optional, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_colors import SystemColor

if TYPE_CHECKING:
    from app.domains.system.models.system_company import SystemCompany
    from app.domains.talent.models.talent_area import TalentArea


class TalentSystem(SystemAudit, SQLModel, table=True):
    __tablename__ = "talent_systems"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_talent_system_company_code"),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    company_id: int = Field(foreign_key="system_companies.id", index=True)
    code: str = Field(index=True)
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    description: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    active: bool = Field(default=True)
    sequence: int = Field(default=10)
    color: SystemColor = Field(
        default=SystemColor.zinc,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )

    company: "SystemCompany" = Relationship()
    areas: List["TalentArea"] = Relationship(back_populates="system")
