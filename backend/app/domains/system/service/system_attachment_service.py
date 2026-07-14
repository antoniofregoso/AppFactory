import uuid as uuid_lib
from pathlib import Path
from typing import BinaryIO

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.domains.system.models.system_attachment import SystemAttachment
from app.domains.system.repository.system_attachment_repository import (
    SystemAttachmentRepository,
)
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.storage import AttachmentStorage, get_attachment_storage


class SystemAttachmentService:
    @staticmethod
    async def create(
        *,
        model_uuid: uuid_lib.UUID,
        record_uuid: uuid_lib.UUID,
        original_name: str,
        content_type: str,
        stream: BinaryIO,
        user_id: int,
        company_id: int | None,
        storage: AttachmentStorage | None = None,
    ) -> SystemAttachment:
        model = await SystemModelRepository.get_by_uuid(model_uuid)
        if model is None:
            raise ResourceNotFoundException(
                resource="SystemModel",
                resource_id=str(model_uuid),
            )

        safe_name = Path(original_name or "").name.strip()
        if not safe_name or safe_name in {".", ".."}:
            raise ValidationException(
                "Attachment filename is required",
                error_code="INVALID_ATTACHMENT_NAME",
            )
        if len(safe_name) > 255:
            raise ValidationException(
                "Attachment filename is too long",
                error_code="INVALID_ATTACHMENT_NAME",
                details={"max_length": 255},
            )
        if content_type not in settings.ATTACHMENT_ALLOWED_CONTENT_TYPES:
            raise ValidationException(
                "Attachment content type is not allowed",
                error_code="ATTACHMENT_TYPE_NOT_ALLOWED",
                details={"content_type": content_type},
            )

        storage = storage or get_attachment_storage()
        stored = await run_in_threadpool(storage.store, stream)
        attachment = SystemAttachment(
            model_id=model.id,
            record_uuid=record_uuid,
            company_id=company_id,
            original_name=safe_name,
            content_type=content_type,
            size_bytes=stored.size_bytes,
            checksum_sha256=stored.checksum_sha256,
            storage_provider=storage.provider,
            storage_key=stored.key,
            create_by=user_id,
        )

        try:
            return await SystemAttachmentRepository.create(attachment)
        except Exception:
            if stored.created:
                references = await SystemAttachmentRepository.count_by_storage_key(
                    stored.key
                )
                if references == 0:
                    await run_in_threadpool(storage.delete, stored.key)
            raise

    @staticmethod
    async def get_all_for_record(
        model_uuid: uuid_lib.UUID,
        record_uuid: uuid_lib.UUID,
        company_id: int | None,
    ) -> list[SystemAttachment]:
        model = await SystemModelRepository.get_by_uuid(model_uuid)
        if model is None:
            raise ResourceNotFoundException(
                resource="SystemModel",
                resource_id=str(model_uuid),
            )
        return await SystemAttachmentRepository.get_by_record(
            model.id,
            record_uuid,
            company_id,
        )

    @staticmethod
    async def get_content(
        attachment_uuid: uuid_lib.UUID,
        company_id: int | None,
        storage: AttachmentStorage | None = None,
    ) -> tuple[SystemAttachment, Path]:
        attachment = await SystemAttachmentRepository.get_by_uuid(
            attachment_uuid,
            company_id,
        )
        if attachment is None:
            raise ResourceNotFoundException(
                resource="SystemAttachment",
                resource_id=str(attachment_uuid),
            )
        storage = storage or get_attachment_storage()
        if attachment.storage_provider != storage.provider:
            raise ResourceNotFoundException(
                resource="Attachment storage provider",
                resource_id=attachment.storage_provider,
            )
        path = await run_in_threadpool(storage.path, attachment.storage_key)
        return attachment, path

    @staticmethod
    async def delete(
        attachment_uuid: uuid_lib.UUID,
        company_id: int | None,
        storage: AttachmentStorage | None = None,
    ) -> bool:
        attachment, references = await SystemAttachmentRepository.delete(
            attachment_uuid,
            company_id,
        )
        if attachment is None:
            raise ResourceNotFoundException(
                resource="SystemAttachment",
                resource_id=str(attachment_uuid),
            )
        storage = storage or get_attachment_storage()
        if references == 0 and attachment.storage_provider == storage.provider:
            await run_in_threadpool(storage.delete, attachment.storage_key)
        return True
