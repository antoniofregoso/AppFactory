import hashlib
from io import BytesIO

import pytest

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.domains.system.storage.local import LocalFilestore


@pytest.fixture
def filestore(tmp_path):
    return LocalFilestore(
        root=tmp_path / "filestore",
        namespace="app_db",
        max_size_bytes=1024,
    )


class TestLocalFilestore:
    def test_stores_content_by_sha256_and_reads_it(self, filestore):
        content = b"invoice-content"
        checksum = hashlib.sha256(content).hexdigest()

        stored = filestore.store(BytesIO(content))

        assert stored.key == f"app_db/{checksum[:2]}/{checksum}"
        assert stored.checksum_sha256 == checksum
        assert stored.size_bytes == len(content)
        assert stored.created is True
        assert filestore.path(stored.key).read_bytes() == content

    def test_deduplicates_identical_content(self, filestore):
        first = filestore.store(BytesIO(b"same-file"))
        second = filestore.store(BytesIO(b"same-file"))

        assert second.key == first.key
        assert second.created is False

    def test_rejects_oversized_files_without_leaving_temporary_data(self, filestore):
        with pytest.raises(ValidationException) as error:
            filestore.store(BytesIO(b"x" * 1025))

        assert error.value.error_code == "ATTACHMENT_TOO_LARGE"
        assert list((filestore.root / ".tmp").iterdir()) == []

    def test_rejects_empty_files(self, filestore):
        with pytest.raises(ValidationException) as error:
            filestore.store(BytesIO(b""))

        assert error.value.error_code == "EMPTY_ATTACHMENT"

    def test_rejects_paths_outside_the_filestore(self, filestore):
        with pytest.raises(ValidationException) as error:
            filestore.path("../../secret.txt")

        assert error.value.error_code == "INVALID_STORAGE_KEY"

    def test_deletes_content(self, filestore):
        stored = filestore.store(BytesIO(b"temporary"))

        filestore.delete(stored.key)

        with pytest.raises(ResourceNotFoundException):
            filestore.path(stored.key)
