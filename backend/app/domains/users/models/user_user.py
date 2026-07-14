from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import text as sa_text
from typing import TYPE_CHECKING, List, Optional
from pydantic import EmailStr, constr
import uuid

if TYPE_CHECKING:
    from app.domains.system.models.system_message import SystemMessage
    from app.domains.system.models.system_notification import SystemNotification
    from app.domains.system.models.system_task import SystemTask
    from app.domains.system.models.system_push_subscription import SystemPushSubscription
    from app.domains.system.models.system_company import SystemCompany
    from app.domains.system.models.system_lang import SystemLang
    from app.domains.users.models.user_log import UserLog
    from app.domains.users.models.user_session import UserSession

from app.domains.system.models.system_message_user_rel import SystemMessageUserRel
from app.domains.system.models.system_notification_user_rel import (
    SystemNotificationUserRel,
)
from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_model_followers import SystemModelFollowers


class ThemeMode(str, Enum):
    light = "light"
    dark = "dark"
    system = "system"


class UserType(str, Enum):
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    AIAGENT = "AIAGENT"


class UserUser(SystemAudit, SQLModel, table=True):
    __tablename__ = "user_user"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    email: EmailStr = Field(unique=True, index=True)
    name: constr(min_length=2, max_length=100)
    password: constr(min_length=8)
    avatar_url: Optional[str] = None
    theme: ThemeMode = Field(default=ThemeMode.system)
    lang_id: Optional[int] = Field(default=None, foreign_key="system_langs.id")
    lang: Optional["SystemLang"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[UserUser.lang_id]"}
    )
    user_type: UserType = Field(default=UserType.HUMAN)
    active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    mcp_access: bool = Field(default=False)
    company_id: Optional[int] = Field(
        default=None, foreign_key="system_companies.id", nullable=True
    )
    company: Optional["SystemCompany"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "[UserUser.company_id]"},
    )

    model_followers: List["SystemModelFollowers"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[SystemModelFollowers.user_id]"},
    )

    # Messages sent by this user
    sent_messages: List["SystemMessage"] = Relationship(
        back_populates="from_user",
        sa_relationship_kwargs={"foreign_keys": "[SystemMessage.from_user_id]"},
    )

    # Messages received by this user
    received_messages: List["SystemMessage"] = Relationship(
        back_populates="to_users",
        link_model=SystemMessageUserRel,
    )

    # Notifications directed to this user (single target via user_id)
    notifications: List["SystemNotification"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[SystemNotification.user_id]"},
    )

    # Notifications where this user is one of many targets
    group_notifications: List["SystemNotification"] = Relationship(
        back_populates="users",
        link_model=SystemNotificationUserRel,
    )

    tasks: List["SystemTask"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[SystemTask.user_id]"},
    )

    push_subscriptions: List["SystemPushSubscription"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[SystemPushSubscription.user_id]"},
    )

    logs: List["UserLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[UserLog.user_id]"},
    )

    sessions: List["UserSession"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[UserSession.user_id]"},
    )
