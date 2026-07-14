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
from app.domains.system.models.system_colors import SystemColor
from app.domains.system.models.system_notification_user_rel import (
    SystemNotificationUserRel,
)

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser


class NotificationStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"


class NotificationPriority(str, enum.Enum):
    info = "info"
    warning = "warning"
    danger = "danger"


class SystemNotification(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_notifications"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": sa_text("CURRENT_TIMESTAMP")},
    )
    status: NotificationStatus = Field(
        default=NotificationStatus.sent,
        sa_column=sa.Column(sa.String(32), nullable=False, server_default="sent"),
    )
    title: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    message: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    read: bool = Field(default=True)
    active: bool = Field(default=False)
    sequence: Optional[int] = Field(default=10)
    color: SystemColor = Field(
        default=SystemColor.zinc,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.info,
        sa_column=sa.Column(sa.String(32), nullable=False, server_default="info"),
    )
    # Deduplication key for system-generated reminders (e.g. task start/due
    # alerts), so the periodic sweep never creates the same reminder twice.
    dedupe_key: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.String(255), nullable=True, unique=True),
    )
    # Single-user target
    user_id: Optional[int] = Field(
        default=None, foreign_key="user_user.id", nullable=True
    )
    user: Optional["UserUser"] = Relationship(
        back_populates="notifications",
        sa_relationship_kwargs={"foreign_keys": "[SystemNotification.user_id]"},
    )

    # Multi-user target
    users: List["UserUser"] = Relationship(
        back_populates="group_notifications",
        link_model=SystemNotificationUserRel,
    )

    def get_title(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.title.get(lang)
            or self.title.get(fallback)
            or next(iter(self.title.values()), "")
        )

    def get_message(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.message.get(lang)
            or self.message.get(fallback)
            or next(iter(self.message.values()), "")
        )
