import hashlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.domains.system.storage.base import StoredFile


class LocalFilestore:
    """Content-addressed local filestore with atomic writes."""

    provider = "local"
    chunk_size = 1024 * 1024

    def __init__(self, root: Path, namespace: str, max_size_bytes: int):
        self.root = root.expanduser().resolve()
        self.namespace = namespace
        self.max_size_bytes = max_size_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        self._temporary_root.mkdir(parents=True, exist_ok=True)

    @property
    def _temporary_root(self) -> Path:
        return self.root / ".tmp"

    def store(self, stream: BinaryIO) -> StoredFile:
        digest = hashlib.sha256()
        size_bytes = 0
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                dir=self._temporary_root,
                prefix="upload-",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while chunk := stream.read(self.chunk_size):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        raise ValidationException(
                            "Attachment exceeds the configured maximum size",
                            error_code="ATTACHMENT_TOO_LARGE",
                            details={"max_size_bytes": self.max_size_bytes},
                        )
                    digest.update(chunk)
                    temporary_file.write(chunk)

            if size_bytes == 0:
                raise ValidationException(
                    "Attachment cannot be empty",
                    error_code="EMPTY_ATTACHMENT",
                )

            checksum = digest.hexdigest()
            key = f"{self.namespace}/{checksum[:2]}/{checksum}"
            destination = self._safe_path(key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            created = not destination.exists()

            if created:
                os.replace(temporary_path, destination)
                temporary_path = None
                destination.chmod(0o640)

            return StoredFile(
                key=key,
                checksum_sha256=checksum,
                size_bytes=size_bytes,
                created=created,
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def path(self, key: str) -> Path:
        path = self._safe_path(key)
        if not path.is_file():
            raise ResourceNotFoundException(
                resource="Attachment content",
                resource_id=key,
            )
        return path

    def delete(self, key: str) -> None:
        path = self._safe_path(key)
        path.unlink(missing_ok=True)
        self._remove_empty_parents(path.parent)

    def _safe_path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValidationException(
                "Invalid attachment storage key",
                error_code="INVALID_STORAGE_KEY",
            ) from exc
        return candidate

    def _remove_empty_parents(self, directory: Path) -> None:
        while directory != self.root and directory != self._temporary_root:
            try:
                directory.rmdir()
            except OSError:
                break
            directory = directory.parent
