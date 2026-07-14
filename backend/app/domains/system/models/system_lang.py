import uuid as uuid_lib
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import text as sa_text
from app.domains.system.models.system_audit import SystemAudit

class SystemLang(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_langs"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    name: str
    code: str = Field(unique=True, index=True)
    iso_code: str = Field(unique=True, index=True)
    url_code: str = Field(unique=True, index=True)
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    week_start: Optional[int] = None
    flag: Optional[str] = None
    active: bool = Field(default=False)
