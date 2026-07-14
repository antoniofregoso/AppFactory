import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from sqlmodel import Field, SQLModel

from app.domains.system.models.system_audit import SystemAudit


class SystemAttachment(SystemAudit, SQLModel, table=True):
    """Metadata for a file stored outside PostgreSQL."""

    __tablename__ = "system_attachments"
    __table_args__ = (
        sa.Index(
            "ix_system_attachments_record",
            "company_id",
            "model_id",
            "record_uuid",
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
    model_id: int = Field(foreign_key="system_models.id", nullable=False)
    record_uuid: uuid.UUID = Field(nullable=False)
    company_id: Optional[int] = Field(
        default=None,
        foreign_key="system_companies.id",
        nullable=True,
    )
    original_name: str = Field(max_length=255, nullable=False)
    content_type: str = Field(max_length=255, nullable=False)
    size_bytes: int = Field(
        sa_column=sa.Column(sa.BigInteger(), nullable=False),
    )
    checksum_sha256: str = Field(max_length=64, nullable=False, index=True)
    storage_provider: str = Field(default="local", max_length=32, nullable=False)
    storage_key: str = Field(max_length=512, nullable=False, index=True)
