import uuid
from datetime import date
from enum import Enum
from typing import Optional, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_colors import SystemColor

if TYPE_CHECKING:
    from app.domains.parties.models.parties_party import PartiesParty
    from app.domains.system.models.system_company import SystemCompany
    from app.domains.talent.models.talent_position import TalentPosition
    from app.domains.users.models.user_user import UserUser


class AgentType(str, Enum):
    HUMAN = "HUMAN"
    AIAGENT = "AIAGENT"


class TalentAgent(SystemAudit, SQLModel, table=True):
    __tablename__ = "talent_agents"
    __table_args__ = (
        sa.UniqueConstraint(
            "company_id", "party_id", name="uq_talent_agent_company_party"
        ),
        sa.CheckConstraint(
            "date_end IS NULL OR date_start IS NULL OR date_end >= date_start",
            name="ck_talent_agent_dates",
        ),
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
    name: str
    type: AgentType = Field(
        default=AgentType.HUMAN,
        sa_column=sa.Column(sa.String(16), nullable=False),
    )
    active: bool = Field(default=True)
    sequence: int = Field(default=10)
    color: SystemColor = Field(
        default=SystemColor.zinc,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    avatar_url: Optional[str] = None
    party_id: int = Field(foreign_key="parties_party.id", nullable=False, index=True)
    company_id: Optional[int] = Field(
        default=None,
        foreign_key="system_companies.id",
        index=True,
    )
    position_id: Optional[int] = Field(
        default=None,
        foreign_key="talent_positions.id",
        index=True,
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user_user.id",
        index=True,
    )
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    party: "PartiesParty" = Relationship()
    company: Optional["SystemCompany"] = Relationship()
    position: Optional["TalentPosition"] = Relationship(back_populates="agents")
    user: Optional["UserUser"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TalentAgent.user_id]"}
    )
