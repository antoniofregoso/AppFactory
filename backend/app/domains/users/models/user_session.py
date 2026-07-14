import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime
from sqlalchemy import text as sa_text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    user_id: int = Field(foreign_key="user_user.id", nullable=False, index=True)
    user: "UserUser" = Relationship(
        back_populates="sessions",
        sa_relationship_kwargs={"foreign_keys": "[UserSession.user_id]"},
    )
    refresh_token_hash: str = Field(unique=True, index=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": sa_text("CURRENT_TIMESTAMP")},
    )
    expires_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    absolute_expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
