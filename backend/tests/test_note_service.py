import uuid
from types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationException
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.repository.system_note_repository import SystemNoteRepository
from app.domains.system.service.system_note_service import SystemNoteService


class TestSystemNoteService:
    async def test_create_assigns_model_record_company_and_author(self, monkeypatch):
        model_uuid = uuid.uuid4()
        record_uuid = uuid.uuid4()

        async def get_model(_uuid):
            assert _uuid == model_uuid
            return SimpleNamespace(id=7)

        async def create(note):
            note.uuid = uuid.uuid4()
            note.created_at = None
            return note

        async def get_author(note):
            assert note.create_by == 3
            return (uuid.uuid4(), "Ana Admin")

        monkeypatch.setattr(SystemModelRepository, "get_by_uuid", get_model)
        monkeypatch.setattr(SystemNoteRepository, "create", create)
        monkeypatch.setattr(SystemNoteRepository, "get_author", get_author)

        note, author = await SystemNoteService.create(
            model_uuid=model_uuid,
            record_uuid=record_uuid,
            content_html=" <p>Nota</p> ",
            user_id=3,
            company_id=5,
        )
        assert note.model_id == 7
        assert note.record_uuid == record_uuid
        assert note.company_id == 5
        assert note.content_html == "<p>Nota</p>"
        assert author[1] == "Ana Admin"

    async def test_rejects_empty_note(self, monkeypatch):
        async def get_model(_uuid):
            return SimpleNamespace(id=7)

        monkeypatch.setattr(
            SystemModelRepository,
            "get_by_uuid",
            get_model,
        )
        with pytest.raises(ValidationException):
            await SystemNoteService.create(
                model_uuid=uuid.uuid4(),
                record_uuid=uuid.uuid4(),
                content_html="<p><br></p>",
                user_id=3,
                company_id=5,
            )
