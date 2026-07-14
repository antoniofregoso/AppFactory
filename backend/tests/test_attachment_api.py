import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import main

from app.domains.system.api.attachments import download_attachment
from app.domains.system.api.dependencies import get_current_user
from app.domains.system.service.system_attachment_service import (
    SystemAttachmentService,
)


class TestAttachmentAuthentication:
    async def test_list_requires_authentication(self, client):
        response = await client.get(
            f"/api/system/attachments/record/{uuid.uuid4()}/{uuid.uuid4()}"
        )

        assert response.status_code == 401


class TestAttachmentUpload:
    async def test_upload_returns_avatar_metadata(self, client, monkeypatch):
        model_uuid = uuid.uuid4()
        record_uuid = uuid.uuid4()
        attachment_uuid = uuid.uuid4()
        avatar_content = b"\xff\xd8\xffavatar-image\xff\xd9"

        async def current_user_override():
            return SimpleNamespace(
                id=3,
                uuid=uuid.uuid4(),
                name="Ana Admin",
                company_id=5,
                active=True,
            )

        async def create_attachment(**values):
            assert values["user_id"] == 3
            assert values["company_id"] == 5
            assert values["stream"].read() == avatar_content
            assert values["content_type"] == "image/jpeg"
            return SimpleNamespace(
                uuid=attachment_uuid,
                record_uuid=record_uuid,
                original_name="avatar.jpg",
                content_type="image/jpeg",
                size_bytes=len(avatar_content),
                checksum_sha256="a" * 64,
                created_at=datetime.now(timezone.utc),
            )

        main.app.dependency_overrides[get_current_user] = current_user_override
        monkeypatch.setattr(SystemAttachmentService, "create", create_attachment)
        try:
            response = await client.post(
                "/api/system/attachments",
                data={
                    "model_uuid": str(model_uuid),
                    "record_uuid": str(record_uuid),
                },
                files={"file": ("avatar.jpg", avatar_content, "image/jpeg")},
            )
        finally:
            main.app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 201
        data = response.json()
        assert data["uuid"] == str(attachment_uuid)
        assert data["model_uuid"] == str(model_uuid)
        assert data["record_uuid"] == str(record_uuid)
        assert data["content_type"] == "image/jpeg"
        assert data["original_name"] == "avatar.jpg"
        assert data["author_name"] == "Ana Admin"
        assert data["content_url"].endswith(f"/{attachment_uuid}/content")

    async def test_avatar_content_is_served_inline(
        self,
        monkeypatch,
        tmp_path: Path,
    ):
        attachment_uuid = uuid.uuid4()
        avatar_path = tmp_path / "avatar.jpg"
        avatar_content = b"\xff\xd8\xffavatar-image\xff\xd9"
        avatar_path.write_bytes(avatar_content)

        async def get_content(_attachment_uuid, company_id):
            assert _attachment_uuid == attachment_uuid
            assert company_id == 5
            return (
                SimpleNamespace(
                    content_type="image/jpeg",
                    original_name="avatar.jpg",
                ),
                avatar_path,
            )

        monkeypatch.setattr(SystemAttachmentService, "get_content", get_content)
        response = await download_attachment(
            attachment_uuid,
            SimpleNamespace(id=3, company_id=5, active=True),
        )

        assert Path(response.path) == avatar_path
        assert response.media_type == "image/jpeg"
        assert response.headers["content-disposition"].startswith("inline;")
        assert response.headers["x-content-type-options"] == "nosniff"

    async def test_upload_requires_authentication(self, client):
        response = await client.post(
            "/api/system/attachments",
            data={"model_uuid": str(uuid.uuid4()), "record_uuid": str(uuid.uuid4())},
            files={"file": ("document.txt", b"content", "text/plain")},
        )

        assert response.status_code == 401

    async def test_download_requires_authentication(self, client):
        response = await client.get(f"/api/system/attachments/{uuid.uuid4()}/content")

        assert response.status_code == 401

    async def test_delete_requires_authentication(self, client):
        response = await client.delete(f"/api/system/attachments/{uuid.uuid4()}")

        assert response.status_code == 401
