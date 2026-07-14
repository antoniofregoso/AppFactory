from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.domains.users.models.user_log import UserLog
from app.domains.users.service.user_log_service import UserLogService


@pytest.mark.asyncio
async def test_heartbeat_creates_open_log_when_user_has_none(monkeypatch):
    created_logs = []

    async def get_open_by_user_id(user_id: int):
        assert user_id == 42
        return None

    async def create(log: UserLog):
        created_logs.append(log)
        return log

    monkeypatch.setattr(
        "app.domains.users.service.user_log_service.UserLogRepository.get_open_by_user_id",
        get_open_by_user_id,
    )
    monkeypatch.setattr(
        "app.domains.users.service.user_log_service.UserLogRepository.create",
        create,
    )

    log = await UserLogService.heartbeat(42)

    assert log is created_logs[0]
    assert log.user_id == 42
    assert log.start_date == log.last_seen_at


@pytest.mark.asyncio
async def test_heartbeat_updates_last_seen_for_open_log(monkeypatch):
    previous_seen_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    open_log = SimpleNamespace(id=7, user_id=42, last_seen_at=previous_seen_at)
    touched_at = []

    async def get_open_by_user_id(user_id: int):
        assert user_id == 42
        return open_log

    async def touch(log_id: int, seen_at: datetime):
        assert log_id == open_log.id
        touched_at.append(seen_at)
        open_log.last_seen_at = seen_at
        return open_log

    monkeypatch.setattr(
        "app.domains.users.service.user_log_service.UserLogRepository.get_open_by_user_id",
        get_open_by_user_id,
    )
    monkeypatch.setattr(
        "app.domains.users.service.user_log_service.UserLogRepository.touch",
        touch,
    )

    log = await UserLogService.heartbeat(42)

    assert log is open_log
    assert touched_at
    assert log.last_seen_at > previous_seen_at


@pytest.mark.asyncio
async def test_close_stale_logs_uses_configured_timeout(monkeypatch):
    cutoffs = []

    async def close_stale(cutoff: datetime):
        cutoffs.append(cutoff)
        return 3

    monkeypatch.setattr(
        "app.domains.users.service.user_log_service.UserLogRepository.close_stale",
        close_stale,
    )

    closed = await UserLogService.close_stale_logs(timeout_seconds=120)

    assert closed == 3
    expected_cutoff = datetime.now(timezone.utc) - timedelta(seconds=120)
    assert abs((cutoffs[0] - expected_cutoff).total_seconds()) < 2
