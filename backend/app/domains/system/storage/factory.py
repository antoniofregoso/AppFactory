from functools import lru_cache

from sqlalchemy.engine import make_url

from app.core.config.settings import settings
from app.domains.system.storage.local import LocalFilestore


@lru_cache()
def get_attachment_storage() -> LocalFilestore:
    namespace = (
        settings.FILESTORE_NAMESPACE
        or make_url(settings.DATABASE_URL).database
        or "default"
    )
    return LocalFilestore(
        root=settings.FILESTORE_ROOT,
        namespace=namespace,
        max_size_bytes=settings.ATTACHMENT_MAX_SIZE_BYTES,
    )
