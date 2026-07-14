from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class StoredFile:
    key: str
    checksum_sha256: str
    size_bytes: int
    created: bool


class AttachmentStorage(Protocol):
    provider: str

    def store(self, stream: BinaryIO) -> StoredFile: ...

    def path(self, key: str) -> Path: ...

    def delete(self, key: str) -> None: ...
