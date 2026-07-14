import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.domains.system.models.system_note import SystemNote
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.repository.system_note_repository import SystemNoteRepository


class SystemNoteService:
    @staticmethod
    async def create(*, model_uuid, record_uuid, content_html, user_id, company_id):
        model = await SystemModelRepository.get_by_uuid(model_uuid)
        if model is None:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=str(model_uuid))
        content = content_html.strip()
        if not content or content == "<p><br></p>":
            raise ValidationException("Note content is required", error_code="INVALID_NOTE_CONTENT")
        if len(content) > 100_000:
            raise ValidationException(
                "Note content is too long",
                error_code="INVALID_NOTE_CONTENT",
                details={"max_length": 100_000},
            )
        note = await SystemNoteRepository.create(SystemNote(
            model_id=model.id,
            record_uuid=record_uuid,
            company_id=company_id,
            content_html=content,
            create_by=user_id,
        ))
        author = await SystemNoteRepository.get_author(note)
        return note, author

    @staticmethod
    async def get_all_for_record(model_uuid, record_uuid, company_id):
        model = await SystemModelRepository.get_by_uuid(model_uuid)
        if model is None:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=str(model_uuid))
        return await SystemNoteRepository.get_by_record(model.id, record_uuid, company_id)

    @staticmethod
    async def delete(note_uuid: uuid_lib.UUID, company_id: int | None):
        if not await SystemNoteRepository.delete(note_uuid, company_id):
            raise ResourceNotFoundException(resource="SystemNote", resource_id=str(note_uuid))
