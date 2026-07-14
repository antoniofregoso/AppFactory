import uuid as uuid_lib
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.system.models.system_app import SystemApp


class SystemAppSettings(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_app_settings"
    __table_args__ = (
        UniqueConstraint("app_id", "name", name="uq_system_app_settings_app_name"),
        Index("ix_system_app_settings_app_id", "app_id"),
        Index("ix_system_app_settings_name", "name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    app_id: int = Field(foreign_key="system_apps.id")
    name: str
    description: Optional[str] = Field(default=None)
    value: Any = Field(default=None, sa_type=JSONB)
    app: "SystemApp" = Relationship(back_populates="settings_ids")


from app.domains.system.models.system_app import SystemApp  
