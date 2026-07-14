from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import Any, Mapping

from sqlalchemy import exists, or_, select

from app.domains.system.models.system_message import SystemMessage
from app.domains.system.models.system_message_user_rel import SystemMessageUserRel
from app.domains.system.models.system_task import SystemTask
from app.domains.users.models.user_user import UserUser


class SearchAuthorizationPolicy(ABC):
    """Defines the same record visibility rule for SQL and loaded records."""

    @abstractmethod
    def apply(self, statement: Any, current_user_id: int) -> Any:
        """Add the authorization predicate to a SQLAlchemy statement."""

    @abstractmethod
    def allows_record(self, record: Any, current_user_id: int) -> bool:
        """Evaluate the policy for an already loaded record."""


class AssignedTaskAuthorizationPolicy(SearchAuthorizationPolicy):
    def apply(self, statement: Any, current_user_id: int) -> Any:
        return statement.where(SystemTask.user_id == current_user_id)

    def allows_record(self, record: Any, current_user_id: int) -> bool:
        return getattr(record, "user_id", None) == current_user_id


class MessageParticipantAuthorizationPolicy(SearchAuthorizationPolicy):
    def apply(self, statement: Any, current_user_id: int) -> Any:
        recipient_exists = exists(
            select(1).where(
                SystemMessageUserRel.message_id == SystemMessage.id,
                SystemMessageUserRel.user_id == current_user_id,
            )
        )
        return statement.where(
            or_(SystemMessage.from_user_id == current_user_id, recipient_exists)
        )

    def allows_record(self, record: Any, current_user_id: int) -> bool:
        if getattr(record, "from_user_id", None) == current_user_id:
            return True
        return any(
            getattr(recipient, "id", None) == current_user_id
            for recipient in (getattr(record, "to_users", None) or [])
        )


class AuthenticatedRecordAuthorizationPolicy(SearchAuthorizationPolicy):
    """Explicit policy for records already visible to every authenticated user."""

    def apply(self, statement: Any, current_user_id: int) -> Any:
        return statement

    def allows_record(self, record: Any, current_user_id: int) -> bool:
        return True


TASK_AUTHORIZATION_POLICY = AssignedTaskAuthorizationPolicy()
MESSAGE_AUTHORIZATION_POLICY = MessageParticipantAuthorizationPolicy()
USER_AUTHORIZATION_POLICY = AuthenticatedRecordAuthorizationPolicy()

RECORD_AUTHORIZATION_POLICIES: Mapping[str, SearchAuthorizationPolicy] = (
    MappingProxyType(
        {
            "system.task": TASK_AUTHORIZATION_POLICY,
            "system.message": MESSAGE_AUTHORIZATION_POLICY,
            "user.user": USER_AUTHORIZATION_POLICY,
        }
    )
)


def authorization_policy_for(model: str) -> SearchAuthorizationPolicy | None:
    return RECORD_AUTHORIZATION_POLICIES.get(model)
