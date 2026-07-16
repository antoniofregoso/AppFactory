import json
from pathlib import Path

from scripts.setup_database import _validate_seed_sources


DOMAINS_DIR = Path(__file__).parents[1] / "app/domains"


def _load(domain: str):
    path = DOMAINS_DIR / domain / "data/access_control.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _roles(domain: str):
    return {item["code"]: item for item in _load(domain)["roles"]}


def test_modular_access_control_sources_are_valid():
    _validate_seed_sources()


def test_platform_admin_remains_globally_assigned():
    source = _load("access")

    assert _roles("access")["platform_admin"]["permissions"] == ["*"]
    assert source["assignments"] == [{
        "user_email": "admin@app.com",
        "role": "platform_admin",
        "scope_type": "GLOBAL",
    }]


def test_talent_roles_are_templates_without_users():
    source = _load("talent")
    roles = _roles("talent")

    assert source["assignments"] == []
    assert roles["talent_user"]["permissions"] == [
        "talent.agent.read",
        "talent.agent.create",
        "talent.agent.update",
    ]
    assert roles["talent_manager"]["permissions"] == ["talent.*"]


def test_parties_roles_are_templates_without_delete_permissions():
    source = _load("parties")
    roles = _roles("parties")

    assert source["assignments"] == []
    assert roles["parties_user"]["permissions"] == [
        "parties.party.read",
        "parties.party.create",
        "parties.party.update",
        "system.country.read",
        "system.country.state.read",
        "system.lang.read",
    ]
    manager_permissions = set(roles["parties_manager"]["permissions"])
    assert "parties.*" in manager_permissions
    assert {
        "system.country.update",
        "system.country.state.update",
        "system.lang.update",
    } <= manager_permissions
    assert not any(permission.endswith(".delete") for permission in manager_permissions)
