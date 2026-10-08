import ast
from pathlib import Path
from uuid import UUID

import pytest

from app.domains.access.models.access_control import (
    AccessPermission,
    AccessRole,
    AccessUserRole,
)
from app.domains.system.models.system_attachment import SystemAttachment
from app.domains.system.models.system_company import SystemCompany
from app.domains.system.models.system_message import SystemMessage
from app.domains.system.models.system_model import (
    SystemModel,
    SystemModelField,
    SystemModelSchema,
)
from app.domains.system.models.system_note import SystemNote
from app.domains.system.models.system_notification import SystemNotification
from app.domains.system.models.system_push_subscription import SystemPushSubscription
from app.domains.system.models.system_task import SystemTask
from app.domains.talent.models.talent_agent import TalentAgent
from app.domains.talent.models.talent_area import TalentArea
from app.domains.talent.models.talent_position import TalentPosition
from app.domains.talent.models.talent_system import TalentSystem
from app.domains.users.models.user_log import UserLog
from app.domains.users.models.user_session import UserSession
from app.domains.users.models.user_user import UserUser


UUID_MODELS = (
    AccessPermission,
    AccessRole,
    AccessUserRole,
    SystemAttachment,
    SystemCompany,
    SystemMessage,
    SystemModel,
    SystemModelField,
    SystemModelSchema,
    SystemNote,
    SystemNotification,
    SystemPushSubscription,
    SystemTask,
    TalentAgent,
    TalentArea,
    TalentPosition,
    TalentSystem,
    UserLog,
    UserSession,
    UserUser,
)


@pytest.mark.parametrize("model", UUID_MODELS)
def test_uuid_model_fields_keep_uuid_annotations_and_factories(model):
    field = model.model_fields["uuid"]

    assert field.annotation is UUID
    assert field.default_factory is not None
    assert isinstance(field.default_factory(), UUID)


def test_uuid_relationship_fields_keep_uuid_annotations():
    assert SystemAttachment.model_fields["record_uuid"].annotation is UUID
    assert SystemNote.model_fields["record_uuid"].annotation is UUID
    assert AccessUserRole.model_fields["scope_record_uuid"].annotation == UUID | None


def test_model_classes_do_not_shadow_the_uuid_module():
    models_root = Path(__file__).parents[1] / "app" / "domains"
    violations = []

    for path in models_root.glob("*/models/*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            uuid_is_shadowed = False
            for statement in class_node.body:
                if uuid_is_shadowed and any(
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "uuid"
                    for node in ast.walk(statement)
                ):
                    violations.append(f"{path}:{statement.lineno}:{class_node.name}")

                targets = []
                if isinstance(statement, ast.Assign):
                    targets = statement.targets
                elif isinstance(statement, ast.AnnAssign):
                    targets = [statement.target]
                if any(isinstance(target, ast.Name) and target.id == "uuid" for target in targets):
                    uuid_is_shadowed = True

    assert not violations, f"uuid module shadowed in: {', '.join(violations)}"
