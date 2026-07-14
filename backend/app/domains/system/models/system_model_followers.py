import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.system.models.system_model import SystemModel
    from app.domains.users.models.user_user import UserUser


class SystemModelFollowers(SystemAudit, SQLModel, table=True):
    """A user following any record registered in ``system_models``."""

    __tablename__ = "system_model_followers"
    __table_args__ = (
        sa.Index(
            "ix_system_model_followers_record",
            "model_id",
            "record_uuid",
        ),
    )

    user_id: int = Field(
        sa_column=sa.Column(
            sa.Integer,
            sa.ForeignKey("user_user.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )
    model_id: int = Field(
        foreign_key="system_models.id",
        primary_key=True,
        nullable=False,
    )
    record_uuid: uuid.UUID = Field(primary_key=True, nullable=False)

    model: "SystemModel" = Relationship(back_populates="model_followers")
    user: "UserUser" = Relationship(
        back_populates="model_followers",
        sa_relationship_kwargs={"foreign_keys": "[SystemModelFollowers.user_id]"},
    )
