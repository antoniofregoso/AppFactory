from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from app.domains.system.models.system_message import SystemMessage
from app.domains.system.models.system_task import SystemTask
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.authorization import (
    MESSAGE_AUTHORIZATION_POLICY,
    TASK_AUTHORIZATION_POLICY,
    USER_AUTHORIZATION_POLICY,
    SearchAuthorizationPolicy,
)
from app.domains.users.models.user_user import UserUser

RecordUrlBuilder = Callable[[str], str]


@dataclass(frozen=True)
class SearchModelRegistration:
    orm_class: type
    authorization_policy: SearchAuthorizationPolicy
    url_builder: RecordUrlBuilder

    def build_url(self, record_uuid: str) -> str:
        return self.url_builder(str(record_uuid))


def _record_url(area: str, model: str) -> RecordUrlBuilder:
    return lambda record_uuid: f"/dashboard/{area}/{model}/{record_uuid}"


SEARCH_MODEL_REGISTRY: Mapping[str, SearchModelRegistration] = MappingProxyType(
    {
        # `area` mirrors each model's sidebar/topbar entry point — see
        # `frontend/src/app/data/sidebar.json` (user.user -> "configuration")
        # and `frontend/src/app/components/topbar.jsx` (system.task/
        # system.message -> "user"). There's no model->area field in
        # `system_models.json`, so this stays a per-registration constant
        # like the frontend's own hardcoded hrefs.
        "system.task": SearchModelRegistration(
            orm_class=SystemTask,
            authorization_policy=TASK_AUTHORIZATION_POLICY,
            url_builder=_record_url("user", "system.task"),
        ),
        "system.message": SearchModelRegistration(
            orm_class=SystemMessage,
            authorization_policy=MESSAGE_AUTHORIZATION_POLICY,
            url_builder=_record_url("user", "system.message"),
        ),
        "user.user": SearchModelRegistration(
            orm_class=UserUser,
            authorization_policy=USER_AUTHORIZATION_POLICY,
            url_builder=_record_url("configuration", "user.user"),
        ),
    }
)


def require_search_model_registration(model: str) -> SearchModelRegistration:
    try:
        return SEARCH_MODEL_REGISTRY[model]
    except KeyError as exc:
        raise ValueError(f"Search model '{model}' is not registered") from exc


def validate_search_model_registry(searchable_models: set[str]) -> None:
    missing = searchable_models - SEARCH_MODEL_REGISTRY.keys()
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(f"Search models missing secure registration: {names}")


async def validate_configured_search_models() -> None:
    models = await SystemModelRepository.get_all()
    validate_search_model_registry({model.name for model in models if model.search})
