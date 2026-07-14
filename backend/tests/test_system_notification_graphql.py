import strawberry
from sqlalchemy.orm import configure_mappers
from sqlmodel import SQLModel

from main import Mutation, Query
from app.domains.system.models.system_notification import (
    NotificationPriority,
    SystemNotification,
)


def test_system_notification_is_registered_in_orm_and_graphql():
    configure_mappers()
    schema = strawberry.Schema(query=Query, mutation=Mutation).as_str()

    assert "system_notifications" in SQLModel.metadata.tables
    notification = SystemNotification(title={}, message={})
    assert notification.priority == NotificationPriority.info
    assert "systemNotifications" in schema
    assert "systemNotification(" in schema
    assert "systemMyNotifications(" in schema
    assert "createSystemNotification" in schema
    assert "updateSystemNotification" in schema
    assert "deleteSystemNotification" in schema


def test_notification_priority_is_exposed_as_a_graphql_selection():
    schema = strawberry.Schema(query=Query, mutation=Mutation).as_str()

    assert "enum NotificationPriority" in schema
    assert "priority: NotificationPriority!" in schema
    assert "priority: NotificationPriority! = info" in schema
