import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import main

from app.domains.system.api.dependencies import get_current_user
from app.domains.system.service.system_note_service import SystemNoteService


async def current_user_override():
    return SimpleNamespace(id=3, company_id=5, active=True)


class TestNoteApi:
    async def test_notes_require_authentication(self, client):
        response = await client.get(f"/api/system/notes/record/{uuid.uuid4()}/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_create_returns_server_author_and_date(self, client, monkeypatch):
        model_uuid = uuid.uuid4()
        record_uuid = uuid.uuid4()
        note_uuid = uuid.uuid4()
        author_uuid = uuid.uuid4()
        created_at = datetime.now(timezone.utc)

        async def create(**values):
            assert values["user_id"] == 3
            assert values["company_id"] == 5
            return SimpleNamespace(
                uuid=note_uuid,
                record_uuid=record_uuid,
                content_html=values["content_html"],
                created_at=created_at,
            ), (author_uuid, "Ana Admin")

        main.app.dependency_overrides[get_current_user] = current_user_override
        monkeypatch.setattr(SystemNoteService, "create", create)
        try:
            response = await client.post("/api/system/notes", json={
                "model_uuid": str(model_uuid),
                "record_uuid": str(record_uuid),
                "content_html": "<p>Seguimiento</p>",
            })
        finally:
            main.app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 201
        assert response.json()["author_name"] == "Ana Admin"
        assert response.json()["content_html"] == "<p>Seguimiento</p>"

    async def test_delete_uses_authenticated_company(self, client, monkeypatch):
        note_uuid = uuid.uuid4()
        calls = []

        async def delete(note_id, company_id):
            calls.append((note_id, company_id))

        main.app.dependency_overrides[get_current_user] = current_user_override
        monkeypatch.setattr(SystemNoteService, "delete", delete)
        try:
            response = await client.delete(f"/api/system/notes/{note_uuid}")
        finally:
            main.app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 204
        assert calls == [(note_uuid, 5)]
