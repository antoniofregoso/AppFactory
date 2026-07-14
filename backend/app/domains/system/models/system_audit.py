from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, text


class SystemAudit(SQLModel):
    created_at: datetime = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    create_by: Optional[int] = Field(default=None, foreign_key="user_user.id")
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    updated_by: Optional[int] = Field(default=None, foreign_key="user_user.id")
