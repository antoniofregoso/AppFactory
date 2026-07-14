import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from app.core.config.settings import settings
from app.domains.system.models.system_search_audit import SystemSearchAudit
from app.domains.system.repository.system_search_audit_repository import (
    SystemSearchAuditRepository,
)
from app.domains.system.search.limits import DEFAULT_SEARCH_LIMITS


class SystemSearchAuditService:
    @staticmethod
    def hash_query(query: str) -> str:
        normalized = " ".join(str(query or "").split())[
            : DEFAULT_SEARCH_LIMITS.max_string_length
        ]
        return hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            normalized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    async def record(
        *,
        request_id: uuid.UUID,
        user_id: int,
        query: str,
        status: str,
        models: list[str],
        duration_ms: int,
        result_count: int,
        error_codes: list[str],
        mode: str = "TEXT",
    ) -> SystemSearchAudit:
        audit = SystemSearchAudit(
            request_id=request_id,
            user_id=user_id,
            mode=mode,
            status=status,
            models=sorted(set(models)),
            duration_ms=max(0, duration_ms),
            result_count=max(0, result_count),
            query_hash=SystemSearchAuditService.hash_query(query),
            error_codes=sorted(set(error_codes)),
        )
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.SEARCH_AUDIT_RETENTION_DAYS
        )
        return await SystemSearchAuditRepository.create_and_purge(
            audit, older_than=cutoff
        )
