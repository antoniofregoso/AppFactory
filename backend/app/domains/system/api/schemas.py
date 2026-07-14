import uuid as uuid_lib
from datetime import datetime

from pydantic import BaseModel

from app.domains.system.models.system_attachment import SystemAttachment


class SystemAttachmentResponse(BaseModel):
    uuid: uuid_lib.UUID
    model_uuid: uuid_lib.UUID
    record_uuid: uuid_lib.UUID
    original_name: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    created_at: datetime
    author_uuid: uuid_lib.UUID | None = None
    author_name: str | None = None
    content_url: str

    @classmethod
    def from_attachment(
        cls,
        attachment: SystemAttachment,
        model_uuid: uuid_lib.UUID,
        author_uuid: uuid_lib.UUID | None = None,
        author_name: str | None = None,
    ) -> "SystemAttachmentResponse":
        return cls(
            uuid=attachment.uuid,
            model_uuid=model_uuid,
            record_uuid=attachment.record_uuid,
            original_name=attachment.original_name,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            checksum_sha256=attachment.checksum_sha256,
            created_at=attachment.created_at,
            author_uuid=author_uuid,
            author_name=author_name,
            content_url=f"/api/system/attachments/{attachment.uuid}/content",
        )


class SystemNoteCreate(BaseModel):
    model_uuid: uuid_lib.UUID
    record_uuid: uuid_lib.UUID
    content_html: str


class SystemNoteResponse(BaseModel):
    uuid: uuid_lib.UUID
    model_uuid: uuid_lib.UUID
    record_uuid: uuid_lib.UUID
    content_html: str
    author_uuid: uuid_lib.UUID | None = None
    author_name: str | None = None
    created_at: datetime
