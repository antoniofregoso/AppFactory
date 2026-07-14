"""Tests for the read-only MCP report aggregations (app/mcp/reports.py)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.domains.system.models.system_task import TaskPriority, TaskStatus
from app.mcp import reports


def make_user(id, company_id, active=True, name="User", email="user@test.com"):
    return SimpleNamespace(
        id=id,
        company_id=company_id,
        active=active,
        name=name,
        email=email,
        user_type="HUMAN",
    )


@pytest.mark.asyncio
async def test_tasks_report_scopes_by_company_and_flags_overdue(monkeypatch):
    users = [make_user(1, company_id=10), make_user(2, company_id=20)]
    now = datetime.now(timezone.utc)

    company_task = SimpleNamespace(
        user_id=1,
        create_by=None,
        status=TaskStatus.pending,
        priority=TaskPriority.high,
        date_due=now - timedelta(days=1),
        user=users[0],
        get_title=lambda: "Overdue task",
    )
    other_company_task = SimpleNamespace(
        user_id=2,
        create_by=None,
        status=TaskStatus.completed,
        priority=TaskPriority.low,
        date_due=now - timedelta(days=1),
        user=users[1],
        get_title=lambda: "Other company task",
    )

    async def get_all_users():
        return users

    async def get_all_tasks():
        return [company_task, other_company_task]

    monkeypatch.setattr(reports.UserService, "get_all", get_all_users)
    monkeypatch.setattr(reports.SystemTaskService, "get_all", get_all_tasks)

    result = await reports.tasks_report(company_id=10)

    assert result["total"] == 1
    assert result["overdue_count"] == 1
    assert result["overdue_tasks"][0]["title"] == "Overdue task"
    assert result["overdue_tasks"][0]["assigned_to"] == "User"
    assert result["by_status"][TaskStatus.pending.value] == 1
    assert result["by_status"][TaskStatus.completed.value] == 0


@pytest.mark.asyncio
async def test_tasks_report_excludes_completed_from_overdue(monkeypatch):
    users = [make_user(1, company_id=10)]
    now = datetime.now(timezone.utc)

    completed_but_late = SimpleNamespace(
        user_id=1,
        create_by=None,
        status=TaskStatus.completed,
        priority=TaskPriority.low,
        date_due=now - timedelta(days=5),
        user=users[0],
        get_title=lambda: "Finished late",
    )

    async def get_all_users():
        return users

    async def get_all_tasks():
        return [completed_but_late]

    monkeypatch.setattr(reports.UserService, "get_all", get_all_users)
    monkeypatch.setattr(reports.SystemTaskService, "get_all", get_all_tasks)

    result = await reports.tasks_report(company_id=10)

    assert result["total"] == 1
    assert result["overdue_count"] == 0


@pytest.mark.asyncio
async def test_team_activity_report_filters_by_period(monkeypatch):
    users = [make_user(1, company_id=10, name="Recent"), make_user(2, company_id=10, name="Stale")]
    now = datetime.now(timezone.utc)

    recent_log = SimpleNamespace(
        start_date=now - timedelta(days=1),
        last_seen_at=now - timedelta(hours=1),
        duration=60_000,
    )
    stale_log = SimpleNamespace(
        start_date=now - timedelta(days=30),
        last_seen_at=now - timedelta(days=30),
        duration=60_000,
    )

    async def get_all_users():
        return users

    async def get_by_user_id(user_id, limit=200):
        return [recent_log] if user_id == 1 else [stale_log]

    monkeypatch.setattr(reports.UserService, "get_all", get_all_users)
    monkeypatch.setattr(reports.UserLogService, "get_by_user_id", get_by_user_id)

    result = await reports.team_activity_report(company_id=10, days=7)

    assert result["total_company_users"] == 2
    assert result["active_user_count"] == 1
    assert result["users"][0]["name"] == "Recent"
    assert result["users"][0]["duration_minutes"] == 1.0


@pytest.mark.asyncio
async def test_users_overview_scopes_by_company(monkeypatch):
    users = [
        make_user(1, company_id=10, active=True, name="Active One"),
        make_user(2, company_id=10, active=False, name="Inactive One"),
        make_user(3, company_id=20, active=True, name="Other Company"),
    ]

    async def get_all_users():
        return users

    async def get_by_user_id(user_id, limit=1):
        return []

    monkeypatch.setattr(reports.UserService, "get_all", get_all_users)
    monkeypatch.setattr(reports.UserLogService, "get_by_user_id", get_by_user_id)

    result = await reports.users_overview(company_id=10)

    assert result["total_users"] == 2
    assert result["active_users"] == 1
    assert result["inactive_users"] == 1
    names = {user["name"] for user in result["users"]}
    assert names == {"Active One", "Inactive One"}
