from typing import Optional
from sqlmodel import Field, SQLModel


class SystemNotificationUserRel(SQLModel, table=True):
    __tablename__ = "system_notification_user_rel"

    notification_id: Optional[int] = Field(default=None, foreign_key="system_notifications.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user_user.id", primary_key=True)
