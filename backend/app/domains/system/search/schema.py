from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, StrictStr
from sqlalchemy import inspect as sa_inspect

from app.domains.system.search.contracts import SearchContractModel
from app.domains.system.search.registry import SEARCH_MODEL_REGISTRY
from app.domains.system.search.validator import (
    OPERATORS_BY_FIELD_TYPE,
    RELATION_FIELD_TYPES,
    SENSITIVE_FIELD_NAMES,
)

MAX_SCHEMA_MODELS = 20
MAX_SCHEMA_FIELDS = 50


def _field_type(field: Any) -> str:
    value = getattr(field, "type", "")
    return str(getattr(value, "value", value))


def _localized(value: Any, language: str) -> str:
    if not isinstance(value, dict):
        return "" if value is None else str(value)
    short = language.split("_", 1)[0].split("-", 1)[0]
    regional = "es_MX" if short == "es" else "en_US" if short == "en" else language
    return str(
        value.get(language)
        or value.get(regional)
        or value.get(short)
        or value.get("en_US")
        or value.get("en")
        or next(iter(value.values()), "")
    )


class SearchableSelectionValueV1(SearchContractModel):
    value: StrictStr
    label: StrictStr


class SearchableFieldV1(SearchContractModel):
    name: StrictStr
    type: StrictStr
    label: StrictStr
    help: StrictStr = ""
    text: bool = False
    operators: list[StrictStr] = Field(default_factory=list)
    selection_values: list[SearchableSelectionValueV1] = Field(default_factory=list)
    relation_fields: list[StrictStr] = Field(default_factory=list)


class SearchableModelV1(SearchContractModel):
    name: StrictStr
    label: StrictStr
    fields: Annotated[list[SearchableFieldV1], Field(max_length=MAX_SCHEMA_FIELDS)]


class SearchableSchemaV1(SearchContractModel):
    version: Literal[1] = 1
    language: StrictStr
    timezone: StrictStr
    models: Annotated[list[SearchableModelV1], Field(max_length=MAX_SCHEMA_MODELS)]


class SearchableSchemaError(ValueError):
    pass


class SearchSchemaService:
    @staticmethod
    def _authorized_relation_fields(
        model: Any,
        field: Any,
        configured_fields: list[str],
        models: list[Any],
    ) -> list[str]:
        registration = SEARCH_MODEL_REGISTRY.get(model.name)
        if registration is None:
            return []
        try:
            relationships = sa_inspect(registration.orm_class).relationships
            relationship_name = next(
                name
                for name in (field.name, field.name.removesuffix("_id"))
                if name in relationships
            )
            relationship = relationships[relationship_name]
        except (KeyError, AttributeError, StopIteration):
            return []

        related_model = next(
            (
                candidate
                for candidate in models
                if (related := SEARCH_MODEL_REGISTRY.get(candidate.name)) is not None
                and related.orm_class is relationship.mapper.class_
            ),
            None,
        )
        if related_model is None:
            return []
        authorized = {
            related_field.name
            for related_field in getattr(related_model, "fields", [])
            if isinstance(getattr(related_field, "search_config", None), dict)
            and related_field.search_config.get("enabled")
            and related_field.name.casefold() not in SENSITIVE_FIELD_NAMES
            and _field_type(related_field) != "password"
        }
        return [name for name in configured_fields if name in authorized]

    @staticmethod
    def build_with_models(
        models: list[Any],
        *,
        language: str,
        timezone_name: str,
        requested_model: str | None = None,
    ) -> SearchableSchemaV1:
        searchable_models = []
        for model in models:
            if not getattr(model, "search", False):
                continue
            if model.name not in SEARCH_MODEL_REGISTRY:
                continue
            if requested_model and model.name != requested_model:
                continue

            fields = []
            for field in getattr(model, "fields", []):
                config = getattr(field, "search_config", None)
                config = config if isinstance(config, dict) else {}
                field_type = _field_type(field)
                if (
                    not config.get("enabled")
                    or field.name.casefold() in SENSITIVE_FIELD_NAMES
                    or field_type == "password"
                ):
                    continue
                configured = config.get("operators")
                allowed = (
                    OPERATORS_BY_FIELD_TYPE.get(field_type, set())
                    if config.get("filter")
                    else set()
                )
                if configured is not None:
                    allowed = {
                        operator for operator in allowed if operator.value in configured
                    }
                relation_fields = []
                if field_type in RELATION_FIELD_TYPES and config.get("filter"):
                    relation_fields = SearchSchemaService._authorized_relation_fields(
                        model,
                        field,
                        list(config.get("relation_fields") or []),
                        models,
                    )
                selection_values = []
                for option in config.get("selection_values") or []:
                    technical = (
                        option.get("value") if isinstance(option, dict) else None
                    )
                    if technical is None:
                        continue
                    selection_values.append(
                        SearchableSelectionValueV1(
                            value=str(technical),
                            label=_localized(option, language) or str(technical),
                        )
                    )
                fields.append(
                    SearchableFieldV1(
                        name=field.name,
                        type=field_type,
                        label=field.name,
                        help=_localized(getattr(field, "help", {}), language),
                        text=bool(config.get("text")),
                        operators=sorted(operator.value for operator in allowed),
                        selection_values=selection_values,
                        relation_fields=relation_fields,
                    )
                )
            if fields:
                searchable_models.append(
                    SearchableModelV1(
                        name=model.name,
                        label=_localized(getattr(model, "label", {}), language)
                        or model.name,
                        fields=fields[:MAX_SCHEMA_FIELDS],
                    )
                )

        if requested_model and not searchable_models:
            raise SearchableSchemaError(
                f"Model '{requested_model}' is not available for search"
            )
        if len(searchable_models) > MAX_SCHEMA_MODELS:
            raise SearchableSchemaError(
                "Too many searchable models; select one model before using AI search"
            )
        return SearchableSchemaV1(
            language=language,
            timezone=timezone_name,
            models=searchable_models,
        )
