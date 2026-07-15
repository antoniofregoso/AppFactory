import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.talent.models.talent_agent import TalentAgent
    from app.domains.talent.models.talent_area import TalentArea


class TalentPosition(SystemAudit, SQLModel, table=True):
    __tablename__ = "talent_positions"
    __table_args__ = (
        UniqueConstraint("area_id", "code", name="uq_talent_position_area_code"),
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
    area_id: int = Field(foreign_key="talent_areas.id", index=True)
    code: str = Field(index=True)
    parent_position_id: Optional[int] = Field(
        default=None,
        foreign_key="talent_positions.id",
        index=True,
    )
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    mission: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    active: bool = Field(default=True)
    sequence: int = Field(default=10)

    area: "TalentArea" = Relationship(back_populates="positions")
    parent_position: Optional["TalentPosition"] = Relationship(
        back_populates="child_positions",
        sa_relationship_kwargs={
            "foreign_keys": "[TalentPosition.parent_position_id]",
            "remote_side": "[TalentPosition.id]",
        },
    )
    child_positions: List["TalentPosition"] = Relationship(
        back_populates="parent_position",
        sa_relationship_kwargs={
            "foreign_keys": "[TalentPosition.parent_position_id]",
        },
    )
    agents: List["TalentAgent"] = Relationship(back_populates="position")
