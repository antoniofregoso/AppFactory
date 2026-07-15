import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.talent.models.talent_position import TalentPosition
    from app.domains.talent.models.talent_system import TalentSystem


class TalentArea(SystemAudit, SQLModel, table=True):
    __tablename__ = "talent_areas"
    __table_args__ = (
        UniqueConstraint("system_id", "code", name="uq_talent_area_system_code"),
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
    system_id: int = Field(foreign_key="talent_systems.id", index=True)
    code: str = Field(index=True)
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    description: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    active: bool = Field(default=True)
    sequence: int = Field(default=10)

    system: "TalentSystem" = Relationship(back_populates="areas")
    positions: List["TalentPosition"] = Relationship(back_populates="area")
