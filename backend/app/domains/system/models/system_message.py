import uuid
import enum
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone
from sqlalchemy import text as sa_text
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa
from sqlmodel import Field, Relationship, Column, SQLModel

from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_message_user_rel import SystemMessageUserRel

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser

class MessageStatus(str, enum.Enum):
    sent = "Sent"
    delivered = "Delivered"
    received = "Received"
    read = "Read"
    replied = "Replied"
    forwarded = "Forwarded"
    archived = "Archived"
    deleted = "Deleted"
    failed = "Failed"
    draft = "Draft"


class SystemMessage(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_messages"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    status: MessageStatus = Field(
        default=MessageStatus.sent,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": sa_text("CURRENT_TIMESTAMP")},
    )
    subject: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    message: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    # Sender
    from_user_id: Optional[int] = Field(default=None, foreign_key="user_user.id", nullable=True)
    from_user: Optional["UserUser"] = Relationship(
        back_populates="sent_messages",
        sa_relationship_kwargs={"foreign_keys": "[SystemMessage.from_user_id]"},
    )

    # Recipients (many-to-many)
    to_users: List["UserUser"] = Relationship(
        back_populates="received_messages",
        link_model=SystemMessageUserRel,
    )

    def get_subject(self, lang: str = "es", fallback: str = "en") -> str:
        return self.subject.get(lang) or self.subject.get(fallback) or next(iter(self.subject.values()), "")

    def get_message(self, lang: str = "es", fallback: str = "en") -> str:
        return self.message.get(lang) or self.message.get(fallback) or next(iter(self.message.values()), "")
