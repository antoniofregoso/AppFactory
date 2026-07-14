from datetime import datetime, timezone
import uuid

import pytest
from sqlalchemy import inspect

from app.core.config.settings import settings
from app.domains.system.models.system_search_audit import SystemSearchAudit
from app.domains.system.repository.system_search_audit_repository import (
    SystemSearchAuditRepository,
)
from app.domains.system.service.system_search_audit_service import (
    SystemSearchAuditService,
)


def test_search_audit_schema_never_persists_query_or_filter_values():
    columns = set(inspect(SystemSearchAudit).columns.keys())

    assert "query" not in columns
    assert "query_text" not in columns
    assert "filter_values" not in columns
    assert "plan" not in columns
    assert "query_hash" in columns


def test_search_audit_hash_is_keyed_normalized_and_deterministic():
    first = SystemSearchAuditService.hash_query("  reporte   urgente ")
    second = SystemSearchAuditService.hash_query("reporte urgente")

    assert first == second
    assert len(first) == 64
    assert "reporte" not in first
    assert first != SystemSearchAuditService.hash_query("reporte público")


@pytest.mark.asyncio
async def test_search_audit_records_only_technical_metadata_and_retention(monkeypatch):
    captured = {}

    async def create_and_purge(audit, *, older_than):
        captured["audit"] = audit
        captured["older_than"] = older_than
        return audit

    monkeypatch.setattr(
        SystemSearchAuditRepository, "create_and_purge", create_and_purge
    )
    request_id = uuid.uuid4()
    before = datetime.now(timezone.utc)

    audit = await SystemSearchAuditService.record(
        request_id=request_id,
        user_id=7,
        query="cliente secreto",
        status="OK",
        models=["system.task", "system.task", "system.message"],
        duration_ms=-4,
        result_count=2,
        error_codes=[],
    )

    assert audit.request_id == request_id
    assert audit.user_id == 7
    assert audit.models == ["system.message", "system.task"]
    assert audit.duration_ms == 0
    assert audit.result_count == 2
    assert audit.query_hash == SystemSearchAuditService.hash_query("cliente secreto")
    assert not hasattr(audit, "query")
    expected_cutoff = before.timestamp() - (
        settings.SEARCH_AUDIT_RETENTION_DAYS * 24 * 60 * 60
    )
    assert abs(captured["older_than"].timestamp() - expected_cutoff) < 2
