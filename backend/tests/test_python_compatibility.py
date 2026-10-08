import ast
from pathlib import Path
from uuid import UUID, uuid4

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
    assert field.default_factory is uuid4
    assert field.default_factory().version == 4


def test_uuid_relationship_fields_keep_uuid_annotations():
    assert SystemAttachment.model_fields["record_uuid"].annotation is UUID
    assert SystemNote.model_fields["record_uuid"].annotation is UUID
    assert AccessUserRole.model_fields["scope_record_uuid"].annotation == UUID | None


def test_models_with_uuid_fields_do_not_import_uuid_without_alias():
    models_root = Path(__file__).parents[1] / "app" / "domains"
    violations = []

    for path in models_root.glob("*/models/*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        imports_uuid_without_alias = any(
            isinstance(node, ast.Import)
            and any(alias.name == "uuid" and alias.asname is None for alias in node.names)
            for node in tree.body
        )
        uuid_field_classes = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and any(
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.target.id == "uuid"
                for statement in node.body
            )
        ]
        if imports_uuid_without_alias and uuid_field_classes:
            violations.append(f"{path}: {', '.join(uuid_field_classes)}")

    assert not violations, f"unaliased uuid import in: {'; '.join(violations)}"
