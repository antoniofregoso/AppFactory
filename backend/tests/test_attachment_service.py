import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationException
from app.domains.system.repository.system_attachment_repository import (
    SystemAttachmentRepository,
)
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.service.system_attachment_service import (
    SystemAttachmentService,
)
from app.domains.system.service import system_attachment_service
from app.domains.system.storage.local import LocalFilestore


@pytest.fixture
def storage(tmp_path):
    return LocalFilestore(tmp_path / "filestore", "app_db", 1024)


@pytest.fixture
def model(monkeypatch):
    system_model = SimpleNamespace(id=7, uuid=uuid.uuid4())

    async def get_by_uuid(_model_uuid):
        return system_model

    monkeypatch.setattr(SystemModelRepository, "get_by_uuid", get_by_uuid)
    return system_model


@pytest.fixture(autouse=True)
def inline_threadpool(monkeypatch):
    async def run_inline(function, *args):
        return function(*args)

    monkeypatch.setattr(
        system_attachment_service,
        "run_in_threadpool",
        run_inline,
    )


class TestSystemAttachmentService:
    async def test_stores_avatar_image_in_local_filestore(
        self,
        monkeypatch,
        storage,
        model,
    ):
        avatar_content = b"\xff\xd8\xffavatar-image\xff\xd9"

        async def create(attachment):
            attachment.id = 1
            return attachment

        monkeypatch.setattr(SystemAttachmentRepository, "create", create)

        attachment = await SystemAttachmentService.create(
            model_uuid=model.uuid,
            record_uuid=uuid.uuid4(),
            original_name="avatar.jpg",
            content_type="image/jpeg",
            stream=BytesIO(avatar_content),
            user_id=3,
            company_id=5,
            storage=storage,
        )

        assert attachment.original_name == "avatar.jpg"
        assert attachment.content_type == "image/jpeg"
        assert attachment.storage_provider == "local"
        assert storage.path(attachment.storage_key).read_bytes() == avatar_content

    async def test_creates_metadata_for_stored_content(
        self,
        monkeypatch,
        storage,
        model,
    ):
        async def create(attachment):
            attachment.id = 1
            return attachment

        monkeypatch.setattr(SystemAttachmentRepository, "create", create)
        record_uuid = uuid.uuid4()

        attachment = await SystemAttachmentService.create(
            model_uuid=model.uuid,
            record_uuid=record_uuid,
            original_name="../../invoice.txt",
            content_type="text/plain",
            stream=BytesIO(b"invoice"),
            user_id=3,
            company_id=5,
            storage=storage,
        )

        assert attachment.model_id == model.id
        assert attachment.record_uuid == record_uuid
        assert attachment.company_id == 5
        assert attachment.original_name == "invoice.txt"
        assert attachment.storage_provider == "local"
        assert storage.path(attachment.storage_key).read_bytes() == b"invoice"

    async def test_rejects_disallowed_content_types(self, storage, model):
        with pytest.raises(ValidationException) as error:
            await SystemAttachmentService.create(
                model_uuid=model.uuid,
                record_uuid=uuid.uuid4(),
                original_name="script.html",
                content_type="text/html",
                stream=BytesIO(b"<script></script>"),
                user_id=3,
                company_id=5,
                storage=storage,
            )

        assert error.value.error_code == "ATTACHMENT_TYPE_NOT_ALLOWED"

    async def test_removes_new_content_when_metadata_creation_fails(
        self,
        monkeypatch,
        storage,
        model,
    ):
        async def fail_create(_attachment):
            raise RuntimeError("database unavailable")

        async def no_references(_storage_key):
            return 0

        monkeypatch.setattr(SystemAttachmentRepository, "create", fail_create)
        monkeypatch.setattr(
            SystemAttachmentRepository,
            "count_by_storage_key",
            no_references,
        )

        with pytest.raises(RuntimeError):
            await SystemAttachmentService.create(
                model_uuid=model.uuid,
                record_uuid=uuid.uuid4(),
                original_name="invoice.txt",
                content_type="text/plain",
                stream=BytesIO(b"orphan"),
                user_id=3,
                company_id=5,
                storage=storage,
            )

        stored_files = [path for path in storage.root.rglob("*") if path.is_file()]
        assert stored_files == []
