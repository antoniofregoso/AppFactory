import uuid as uuid_lib
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.system.models.system_app_settings import SystemAppSettings
    from app.domains.system.models.system_company import SystemCompany


class SystemApp(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_apps"
    __table_args__ = (
        Index("ix_system_apps_keys_gin", "keys", postgresql_using="gin"),
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
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    description: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    keys: Optional[dict] = Field(default=None, sa_type=JSONB)
    active: bool = Field(default=True)
    public: bool = Field(default=True)
    company_id: Optional[int] = Field(default=None, foreign_key="system_companies.id")
    company: Optional["SystemCompany"] = Relationship(back_populates="apps")
    schema_org: Optional[dict] = Field(default=None, sa_type=JSONB)
    settings_ids: list["SystemAppSettings"] = Relationship(back_populates="app")


from app.domains.system.models.system_app_settings import SystemAppSettings  # noqa: E402
