import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import text as sa_text
import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.users.models.user_user import UserUser


class SystemPushSubscription(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_push_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    endpoint: str = Field(
        sa_column=sa.Column(sa.Text, nullable=False, unique=True),
    )
    p256dh: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    auth: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    user_agent: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text, nullable=True))

    user_id: int = Field(foreign_key="user_user.id", nullable=False)
    user: Optional["UserUser"] = Relationship(
        back_populates="push_subscriptions",
        sa_relationship_kwargs={"foreign_keys": "[SystemPushSubscription.user_id]"},
    )
