import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from sqlmodel import Field, SQLModel

from app.domains.system.models.system_audit import SystemAudit


class SystemNote(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_notes"
    __table_args__ = (
        sa.Index("ix_system_notes_record", "company_id", "model_id", "record_uuid"),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={"server_default": sa_text("gen_random_uuid()"), "unique": True},
        index=True,
    )
    model_id: int = Field(foreign_key="system_models.id", nullable=False)
    record_uuid: uuid.UUID = Field(nullable=False)
    company_id: Optional[int] = Field(
        default=None, foreign_key="system_companies.id", nullable=True
    )
    content_html: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
