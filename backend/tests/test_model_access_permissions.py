from types import SimpleNamespace

import pytest

from app.domains.access.service import AccessService
from app.domains.system.service.system_model_service import _require_model_permission
from app.domains.talent.graphql.queries import require_talent_permission


@pytest.mark.asyncio
async def test_controlled_models_require_the_conventional_action_permission(monkeypatch):
    calls = []

    async def fake_require(user, permission, **scope):
        calls.append((user.id, permission, scope))

    monkeypatch.setattr(AccessService, "require", fake_require)
    user = SimpleNamespace(id=7, company_id=3)

    await _require_model_permission(
        "talent.agent", "delete", current_user=user
    )
    await _require_model_permission(
        "parties.party", "update", current_user=user
    )
    await _require_model_permission(
        "system.country.state", "read", current_user=user
    )

    assert calls == [
        (7, "talent.agent.delete", {"company_id": 3}),
        (7, "parties.party.update", {"company_id": 3}),
        (7, "system.country.state.read", {"company_id": 3}),
    ]


@pytest.mark.asyncio
async def test_uncontrolled_models_keep_their_existing_access_policy(monkeypatch):
    async def unexpected_require(*args, **kwargs):
        raise AssertionError("AccessService.require should not be called")

    monkeypatch.setattr(AccessService, "require", unexpected_require)

    await _require_model_permission(
        "system.currency",
        "read",
        current_user=SimpleNamespace(id=7, company_id=3),
    )


@pytest.mark.asyncio
async def test_talent_graphql_requires_the_exact_action_permission(monkeypatch):
    calls = []

    async def fake_require(user, permission, **scope):
        calls.append((user.id, permission, scope))

    monkeypatch.setattr(AccessService, "require", fake_require)
    user = SimpleNamespace(id=7, company_id=3)

    company_id = await require_talent_permission(user, "agent", "delete")

    assert company_id == 3
    assert calls == [(7, "talent.agent.delete", {"company_id": 3})]
