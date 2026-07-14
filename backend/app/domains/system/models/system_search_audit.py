import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class SystemSearchAudit(SQLModel, table=True):
    """Technical search metadata. Query text and filter values are never persisted."""

    __tablename__ = "system_search_audits"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    request_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=sa.Column(sa.Uuid, nullable=False, unique=True, index=True),
    )
    user_id: int = Field(foreign_key="user_user.id", nullable=False, index=True)
    mode: str = Field(default="TEXT", max_length=32, nullable=False)
    status: str = Field(max_length=32, nullable=False, index=True)
    models: list[str] = Field(
        default_factory=list,
        sa_column=sa.Column(
            JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    duration_ms: int = Field(default=0, ge=0, nullable=False)
    result_count: int = Field(default=0, ge=0, nullable=False)
    query_hash: str = Field(max_length=64, nullable=False, index=True)
    error_codes: list[str] = Field(
        default_factory=list,
        sa_column=sa.Column(
            JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        sa_column_kwargs={"server_default": sa.text("CURRENT_TIMESTAMP")},
    )
