from enum import Enum
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import DateTime, event
from sqlalchemy import text as sa_text
from typing import TYPE_CHECKING, Optional

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser


class UserLogStatus(str, Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"


class UserLog(SystemAudit, SQLModel, table=True):
    __tablename__ = "user_logs"

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
        back_populates="logs",
        sa_relationship_kwargs={"foreign_keys": "[UserLog.user_id]"},
    )
    status: UserLogStatus = Field(
        default=UserLogStatus.ONLINE,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    start_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": sa_text("CURRENT_TIMESTAMP")},
    )
    last_seen_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
    end_date: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
    duration: Optional[int] = Field(default=None, nullable=True)


def _is_offline(status: UserLogStatus | str) -> bool:
    return status == UserLogStatus.OFFLINE or status == UserLogStatus.OFFLINE.value


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@event.listens_for(UserLog, "before_insert")
@event.listens_for(UserLog, "before_update")
def set_offline_dates_and_duration(mapper, connection, target: UserLog) -> None:
    if target.created_at is None and target.start_date is None:
        target.created_at = datetime.now(timezone.utc)
        target.start_date = target.created_at
    elif target.created_at is None:
        target.created_at = target.start_date

    if target.start_date is None:
        target.start_date = target.created_at

    if target.last_seen_at is None:
        target.last_seen_at = target.start_date

    if not _is_offline(target.status):
        return

    if target.end_date is None:
        target.end_date = target.last_seen_at

    start_date = _ensure_aware(target.start_date)
    end_date = _ensure_aware(target.end_date)
    target.duration = max(0, int((end_date - start_date).total_seconds() * 1000))
