import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_colors import SystemColor

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser


class TaskPriority(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    urgent = "Urgent"


class TaskStatus(str, enum.Enum):
    pending = "Pending"
    in_progress = "In Progress"
    completed = "Completed"
    failed = "Failed"


class SystemTask(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_tasks"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    status: TaskStatus = Field(
        default=TaskStatus.pending,
        sa_column=sa.Column(sa.String(32), nullable=False, server_default="Pending"),
    )
    color: SystemColor = Field(
        default=SystemColor.zinc,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    sequence: Optional[int] = Field(default=10)
    title: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    description: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    priority: TaskPriority = Field(
        default=TaskPriority.low,
        sa_column=sa.Column(sa.String(32), nullable=False, server_default="Low"),
    )
    date_assign: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
    date_due: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
    # Single-user target
    user_id: Optional[int] = Field(
        default=None, foreign_key="user_user.id", nullable=True
    )
    user: Optional["UserUser"] = Relationship(
        back_populates="tasks",
        sa_relationship_kwargs={"foreign_keys": "[SystemTask.user_id]"},
    )

    def get_title(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.title.get(lang)
            or self.title.get(fallback)
            or next(iter(self.title.values()), "")
        )

    def get_description(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.description.get(lang)
            or self.description.get(fallback)
            or next(iter(self.description.values()), "")
        )
