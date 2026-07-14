from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.exceptions import AuthorizationException
from app.domains.users.graphql import queries as queries_module
from app.domains.users.graphql.queries import UserQuery
from app.domains.users.graphql.types import UserActivityPeriod
from app.domains.users.models.user_log import UserLogStatus
from app.domains.users.repository.user_log_repository import UserLogRepository
from app.domains.users.service.user_activity_graphics_service import (
    UserActivityGraphicsService,
)


def log(user_id, start_hour, end_hour, *, day=13, online=False):
    start = datetime(2026, 7, day, start_hour, tzinfo=timezone.utc)
    end = datetime(2026, 7, day, end_hour, tzinfo=timezone.utc)
    return SimpleNamespace(
        user_id=user_id,
        start_date=start,
        last_seen_at=end,
        end_date=None if online else end,
        status=UserLogStatus.ONLINE if online else UserLogStatus.OFFLINE,
    )


@pytest.mark.asyncio
async def test_user_activity_graphics_use_real_session_aggregates(monkeypatch):
    captured = {}
    logs = [
        log(1, 8, 9),
        log(1, 10, 11),
        log(2, 12, 15, online=True),
        log(3, 8, 9, day=12),
    ]

    async def get_human_activity_between(start, end, company_id):
        captured.update(start=start, end=end, company_id=company_id)
        return logs

    monkeypatch.setattr(
        UserLogRepository,
        "get_human_activity_between",
        get_human_activity_between,
    )
    now = datetime(2026, 7, 13, 15, tzinfo=timezone.utc)

    result = await UserActivityGraphicsService.get("today", company_id=9, now=now)

    assert result["period"] == "today"
    assert captured["company_id"] == 9
    assert captured["end"] == now
    kpis = {item["id"]: item for item in result["kpis"]}
    assert kpis["kpiUsersOnline"]["value"] == 1
    assert kpis["kpiUsersOnline"]["unit"] == {
        "en": "Users",
        "es": "Usuarios",
    }
    assert kpis["kpiUsersAverageSessionTime"]["value"] == 100
    assert kpis["kpiUsersAverageSessionTime"]["unit"] == {
        "en": "Minutes",
        "es": "Minutos",
    }
    assert kpis["kpiUsersActiveUsers"]["value"] == 2
    assert kpis["kpiUsersActiveUsers"]["unit"] == {
        "en": "Users",
        "es": "Usuarios",
    }
    assert kpis["kpiRecurringUsers"]["value"] == 1
    assert kpis["kpiRecurringUsers"]["unit"] == {
        "en": "Users",
        "es": "Usuarios",
    }

    graphics = {item["id"]: item for item in result["graphics"]}
    heatmap = graphics["graphicUsersPerHour"]
    assert heatmap["type"] == "heatmap"
    monday = heatmap["data"][0]
    assert monday["name"] == {"en": "Mon", "es": "Lun"}
    assert monday["data"][8]["y"] == 1
    assert len(monday["data"]) == 24
    assert len(heatmap["data"]) == 7

    monthly = graphics["graphicUsersMAU"]
    assert monthly["type"] == "bar"
    assert monthly["mode"] == "vertical"
    assert monthly["data"] == [2]
    assert monthly["categories"] == {"en": ["Jul"], "es": ["Jul"]}


@pytest.mark.asyncio
async def test_user_activity_graphics_query_is_admin_only(monkeypatch):
    async def current_user(info):
        return SimpleNamespace(is_admin=False, company_id=9)

    monkeypatch.setattr(queries_module, "get_current_user", current_user)

    with pytest.raises(AuthorizationException, match="Administrator"):
        await UserQuery().user_activity_graphics(
            SimpleNamespace(context={}), UserActivityPeriod.today
        )


@pytest.mark.asyncio
async def test_user_activity_graphics_query_returns_generated_payload(monkeypatch):
    payload = {"period": "weekly", "kpis": [], "graphics": []}
    captured = {}

    async def current_user(info):
        return SimpleNamespace(is_admin=True, company_id=9)

    async def get(period, company_id):
        captured.update(period=period, company_id=company_id)
        return payload

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(UserActivityGraphicsService, "get", get)

    result = await UserQuery().user_activity_graphics(
        SimpleNamespace(context={}), UserActivityPeriod.weekly
    )

    assert result is payload
    assert captured == {"period": "weekly", "company_id": 9}
