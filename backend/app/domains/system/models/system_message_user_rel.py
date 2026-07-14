from typing import Optional
from sqlmodel import Field, SQLModel


class SystemMessageUserRel(SQLModel, table=True):
    __tablename__ = "system_message_user_rel"

    message_id: Optional[int] = Field(default=None, foreign_key="system_messages.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user_user.id", primary_key=True)
