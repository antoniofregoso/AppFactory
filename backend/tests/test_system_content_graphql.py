import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import strawberry

from app.domains.system.graphql.mappers import (
    system_attachment_to_type,
    system_note_to_type,
)
from app.domains.system.graphql.mutations import SystemMutation
from app.domains.system.graphql.queries import SystemQuery


def test_notes_and_attachments_are_exposed_only_through_graphql():
    @strawberry.type
    class Query(SystemQuery):
        pass

    @strawberry.type
    class Mutation(SystemMutation):
        pass

    schema = strawberry.Schema(query=Query, mutation=Mutation).as_str()
    for operation in (
        "systemAttachments",
        "systemAttachmentContent",
        "systemNotes",
        "uploadSystemAttachment",
        "deleteSystemAttachment",
        "createSystemNote",
        "deleteSystemNote",
    ):
        assert operation in schema


def test_content_mappers_preserve_frontend_contract():
    model_uuid = uuid.uuid4()
    record_uuid = uuid.uuid4()
    attachment_uuid = uuid.uuid4()
    author_uuid = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    attachment = SimpleNamespace(
        uuid=attachment_uuid,
        record_uuid=record_uuid,
        original_name="avatar.png",
        content_type="image/png",
        size_bytes=12,
        checksum_sha256="a" * 64,
        created_at=created_at,
    )
    note = SimpleNamespace(
        uuid=uuid.uuid4(),
        record_uuid=record_uuid,
        content_html="<p>Nota</p>",
        created_at=created_at,
    )

    attachment_type = system_attachment_to_type(
        attachment, model_uuid, author_uuid, "Ana"
    )
    note_type = system_note_to_type(note, model_uuid, (author_uuid, "Ana"))

    assert attachment_type.content_url == f"attachment:{attachment_uuid}"
    assert attachment_type.author_name == "Ana"
    assert note_type.content_html == "<p>Nota</p>"
    assert note_type.author_uuid == author_uuid
