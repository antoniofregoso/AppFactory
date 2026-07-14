import strawberry
import uuid as uuid_lib
from datetime import datetime
from enum import Enum
from typing import Optional

from app.domains.users.models.user_log import UserLogStatus

UserLogStatusType = strawberry.enum(UserLogStatus)


@strawberry.enum
class UserActivityPeriod(str, Enum):
    today = "today"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    annual = "annual"


@strawberry.type
class UserType:
    id: int
    uuid: uuid_lib.UUID
    name: str
    email: str
    avatar_url: Optional[str]
    theme: str
    lang: Optional[str]
    active: bool
    is_admin: bool


@strawberry.type
class UserLogType:
    uuid: uuid_lib.UUID
    status: UserLogStatusType
    start_date: datetime
    last_seen_at: Optional[datetime]
    end_date: Optional[datetime]
    duration: Optional[int]
    created_at: datetime


@strawberry.input
class RegisterInput:
    name: str
    email: str
    password: str


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class RefreshSessionInput:
    refresh_token: Optional[str] = None


@strawberry.input
class LogoutInput:
    refresh_token: Optional[str] = None


@strawberry.type
class LoginType:
    email: str
    token: str
    access_token: str
    refresh_token: Optional[str] = None
