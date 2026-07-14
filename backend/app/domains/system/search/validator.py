from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import inspect

from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.contracts import (
    ModelSearchQuery,
    SearchFilter,
    SearchOperator,
    SearchOrder,
    SearchPlanV1,
)
from app.domains.system.search.limits import DEFAULT_SEARCH_LIMITS
from app.domains.system.search.registry import (
    SEARCH_MODEL_REGISTRY,
    SearchModelRegistration,
    require_search_model_registration,
)

OPERATORS_BY_FIELD_TYPE = {
    "string": {SearchOperator.EQ, SearchOperator.CONTAINS, SearchOperator.STARTS_WITH},
    "text": {SearchOperator.EQ, SearchOperator.CONTAINS, SearchOperator.STARTS_WITH},
    "html": {SearchOperator.EQ, SearchOperator.CONTAINS, SearchOperator.STARTS_WITH},
    "selection": {SearchOperator.EQ, SearchOperator.IN, SearchOperator.NOT_IN},
    "status_badge": {SearchOperator.EQ, SearchOperator.IN, SearchOperator.NOT_IN},
    "color": {SearchOperator.EQ, SearchOperator.IN, SearchOperator.NOT_IN},
    "integer": {
        SearchOperator.EQ,
        SearchOperator.GT,
        SearchOperator.GTE,
        SearchOperator.LT,
        SearchOperator.LTE,
        SearchOperator.BETWEEN,
    },
    "decimal": {
        SearchOperator.EQ,
        SearchOperator.GT,
        SearchOperator.GTE,
        SearchOperator.LT,
        SearchOperator.LTE,
        SearchOperator.BETWEEN,
    },
    "monetary": {
        SearchOperator.EQ,
        SearchOperator.GT,
        SearchOperator.GTE,
        SearchOperator.LT,
        SearchOperator.LTE,
        SearchOperator.BETWEEN,
    },
    "percentage": {
        SearchOperator.EQ,
        SearchOperator.GT,
        SearchOperator.GTE,
        SearchOperator.LT,
        SearchOperator.LTE,
        SearchOperator.BETWEEN,
    },
    "boolean": {SearchOperator.EQ},
    "date": {
        SearchOperator.EQ,
        SearchOperator.BEFORE,
        SearchOperator.AFTER,
        SearchOperator.BETWEEN,
        SearchOperator.TODAY,
        SearchOperator.THIS_WEEK,
        SearchOperator.THIS_MONTH,
    },
    "datetime": {
        SearchOperator.EQ,
        SearchOperator.BEFORE,
        SearchOperator.AFTER,
        SearchOperator.BETWEEN,
        SearchOperator.TODAY,
        SearchOperator.THIS_WEEK,
        SearchOperator.THIS_MONTH,
    },
    "many2one": {SearchOperator.EQ, SearchOperator.IN},
    "many2one_avatar": {SearchOperator.EQ, SearchOperator.IN},
    "many2many": {SearchOperator.CONTAINS_ANY, SearchOperator.CONTAINS_ALL},
    "many2many_pills": {SearchOperator.CONTAINS_ANY, SearchOperator.CONTAINS_ALL},
}

ORDERABLE_FIELD_TYPES = {
    "string",
    "text",
    "selection",
    "status_badge",
    "color",
    "integer",
    "decimal",
    "monetary",
    "percentage",
    "date",
    "datetime",
}
RELATION_FIELD_TYPES = {
    "many2one",
    "many2one_avatar",
    "many2many",
    "many2many_pills",
}
SENSITIVE_FIELD_NAMES = {
    "password",
    "access_token",
    "refresh_token",
    "verify_token",
    "app_secret",
    "secret",
}


class SearchPlanValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedSearchField:
    path: str
    model_name: str
    field: Any
    registration: SearchModelRegistration
    related_model_name: str | None = None
    related_registration: SearchModelRegistration | None = None
    selection_values: tuple[dict, ...] = ()

    @property
    def field_type(self) -> str:
        value = getattr(self.field, "type", "")
        return str(getattr(value, "value", value))


@dataclass(frozen=True)
class ValidatedSearchFilter:
    filter: SearchFilter
    resolved_field: ResolvedSearchField
    value: Any


@dataclass(frozen=True)
class ValidatedSearchOrder:
    order: SearchOrder
    resolved_field: ResolvedSearchField


@dataclass(frozen=True)
class ValidatedModelSearchQuery:
    query: ModelSearchQuery
    text_fields: tuple[ResolvedSearchField, ...]
    filters: tuple[ValidatedSearchFilter, ...]
    orders: tuple[ValidatedSearchOrder, ...]
    result_limit: int


@dataclass(frozen=True)
class ValidatedSearchPlan:
    plan: SearchPlanV1
    queries: tuple[ValidatedModelSearchQuery, ...]


def _field_map(model: Any) -> dict[str, Any]:
    return {field.name: field for field in getattr(model, "fields", [])}


def _search_config(field: Any) -> dict:
    config = getattr(field, "search_config", None)
    return config if isinstance(config, dict) else {}


def _selection_values(model: Any, field: Any) -> tuple[dict, ...]:
    configured = _search_config(field).get("selection_values") or []
    if configured:
        return tuple(configured)
    if getattr(model, "group_by", None) == getattr(field, "name", None):
        return tuple(getattr(model, "group_by_values", None) or [])
    return ()


def _localized_option_label(option: dict, language: str) -> str | None:
    locale = "es_MX" if language.startswith("es") else "en_US"
    labels = option.get("label") if isinstance(option.get("label"), dict) else option
    return next(
        (
            str(labels[key])
            for key in (locale, language, "en_US", "en", "es_MX", "es")
            if labels.get(key) is not None
        ),
        None,
    )


def _resolve_selection_scalar(
    value: Any,
    options: tuple[dict, ...],
    language: str,
    path: str,
) -> Any:
    if not options:
        raise SearchPlanValidationError(
            f"Selection field '{path}' has no persisted values"
        )
    normalized = str(value).casefold()
    technical_matches = [
        option
        for option in options
        if str(option.get("value")).casefold() == normalized
    ]
    if technical_matches:
        return technical_matches[0].get("value")

    localized_matches = [
        option
        for option in options
        if (_localized_option_label(option, language) or "").casefold() == normalized
    ]
    if len(localized_matches) > 1:
        raise SearchPlanValidationError(
            f"Localized selection value '{value}' is ambiguous for field '{path}'"
        )
    if localized_matches:
        return localized_matches[0].get("value")
    raise SearchPlanValidationError(
        f"Value '{value}' is not valid for selection field '{path}'"
    )


def _normalized_filter_value(
    search_filter: SearchFilter,
    field: ResolvedSearchField,
    language: str,
) -> Any:
    value = search_filter.value
    if field.field_type not in {"selection", "status_badge", "color"}:
        return value
    if isinstance(value, list):
        return [
            _resolve_selection_scalar(
                item, field.selection_values, language, field.path
            )
            for item in value
        ]
    return _resolve_selection_scalar(
        value, field.selection_values, language, field.path
    )


def _is_sensitive(field: Any) -> bool:
    name = str(getattr(field, "name", "")).casefold()
    field_type = str(
        getattr(getattr(field, "type", ""), "value", getattr(field, "type", ""))
    )
    return (
        field_type == "password"
        or name in SENSITIVE_FIELD_NAMES
        or name.endswith("_token")
        or name.endswith("_secret")
    )


def _related_model_name(
    registration: SearchModelRegistration, field_name: str
) -> str | None:
    mapper = inspect(registration.orm_class)
    relationship_names = [field_name]
    if field_name.endswith("_id"):
        relationship_names.append(field_name[:-3])

    related_class = next(
        (
            mapper.relationships[name].mapper.class_
            for name in relationship_names
            if name in mapper.relationships
        ),
        None,
    )
    if related_class is None:
        return None
    return next(
        (
            model_name
            for model_name, item in SEARCH_MODEL_REGISTRY.items()
            if item.orm_class is related_class
        ),
        None,
    )


def _configured_operators(field: Any) -> set[SearchOperator]:
    field_type = str(
        getattr(getattr(field, "type", ""), "value", getattr(field, "type", ""))
    )
    allowed = set(OPERATORS_BY_FIELD_TYPE.get(field_type, set()))
    configured = _search_config(field).get("operators")
    if configured is not None:
        try:
            allowed &= {SearchOperator(value) for value in configured}
        except ValueError as exc:
            raise SearchPlanValidationError(
                f"Field '{field.name}' declares an unknown search operator"
            ) from exc
    return allowed


def _validate_scalar(field_type: str, value: Any, path: str) -> Any:
    try:
        if field_type in {"string", "text", "html"}:
            if not isinstance(value, str):
                raise TypeError
            return value
        if field_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError
            return value
        if field_type in {"decimal", "monetary", "percentage"}:
            if not isinstance(value, str):
                raise TypeError
            return Decimal(value)
        if field_type == "boolean":
            if not isinstance(value, bool):
                raise TypeError
            return value
        if field_type == "date":
            if not isinstance(value, str):
                raise TypeError
            return date.fromisoformat(value)
        if field_type == "datetime":
            if not isinstance(value, str):
                raise TypeError
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("datetime requires an offset")
            return parsed
        if field_type in RELATION_FIELD_TYPES:
            if not isinstance(value, str):
                raise TypeError
            return UUID(value)
        return value
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise SearchPlanValidationError(
            f"Value for field '{path}' is incompatible with type '{field_type}'"
        ) from exc


def _validate_filter_value(
    search_filter: SearchFilter, field: ResolvedSearchField
) -> None:
    value = search_filter.value
    values: Iterable[Any] = value if isinstance(value, list) else [value]
    parsed = [
        _validate_scalar(field.field_type, item, field.path)
        for item in values
        if item is not None
    ]
    if search_filter.operator == SearchOperator.BETWEEN and parsed[0] > parsed[1]:
        raise SearchPlanValidationError(
            f"between start exceeds end for field '{field.path}'"
        )


class SearchPlanValidator:
    @staticmethod
    async def validate(plan: SearchPlanV1, language: str = "es") -> ValidatedSearchPlan:
        models = await SystemModelRepository.get_all()
        return SearchPlanValidator.validate_with_models(plan, models, language)

    @staticmethod
    def validate_with_models(
        plan: SearchPlanV1, models: Iterable[Any], language: str = "es"
    ) -> ValidatedSearchPlan:
        if plan.needs_clarification:
            return ValidatedSearchPlan(plan=plan, queries=())

        models_by_name = {model.name: model for model in models}
        validated_queries = []
        result_limits = DEFAULT_SEARCH_LIMITS.allocate_results(
            [query.limit for query in plan.queries]
        )
        for query, result_limit in zip(plan.queries, result_limits, strict=True):
            model = models_by_name.get(query.model)
            if model is None or not getattr(model, "search", False):
                raise SearchPlanValidationError(
                    f"Model '{query.model}' is not enabled for search"
                )
            registration = require_search_model_registration(query.model)
            fields = _field_map(model)

            text_fields = tuple(
                ResolvedSearchField(
                    path=field.name,
                    model_name=query.model,
                    field=field,
                    registration=registration,
                    selection_values=_selection_values(model, field),
                )
                for field in fields.values()
                if _search_config(field).get("enabled")
                and _search_config(field).get("text")
                and not _is_sensitive(field)
            )

            if query.text is not None and not text_fields:
                raise SearchPlanValidationError(
                    f"Model '{query.model}' has no searchable text fields"
                )

            validated_filters = []
            group_filters = query.filters.and_filters or query.filters.or_filters or []
            for search_filter in group_filters:
                resolved = SearchPlanValidator._resolve_field(
                    query.model,
                    search_filter.field,
                    registration,
                    fields,
                    models_by_name,
                )
                allowed = _configured_operators(resolved.field)
                if search_filter.operator not in allowed:
                    raise SearchPlanValidationError(
                        f"Operator '{search_filter.operator.value}' is not allowed for "
                        f"field '{search_filter.field}'"
                    )
                _validate_filter_value(search_filter, resolved)
                validated_filters.append(
                    ValidatedSearchFilter(
                        search_filter,
                        resolved,
                        _normalized_filter_value(search_filter, resolved, language),
                    )
                )

            validated_orders = []
            for order in query.order:
                resolved = SearchPlanValidator._resolve_field(
                    query.model,
                    order.field,
                    registration,
                    fields,
                    models_by_name,
                )
                if resolved.field_type not in ORDERABLE_FIELD_TYPES:
                    raise SearchPlanValidationError(
                        f"Field '{order.field}' cannot be used for ordering"
                    )
                if resolved.related_registration is not None:
                    raise SearchPlanValidationError(
                        f"Related field '{order.field}' cannot be used for ordering"
                    )
                validated_orders.append(ValidatedSearchOrder(order, resolved))

            validated_queries.append(
                ValidatedModelSearchQuery(
                    query=query,
                    text_fields=text_fields,
                    filters=tuple(validated_filters),
                    orders=tuple(validated_orders),
                    result_limit=result_limit,
                )
            )
        return ValidatedSearchPlan(plan=plan, queries=tuple(validated_queries))

    @staticmethod
    def _resolve_field(
        model_name: str,
        path: str,
        registration: SearchModelRegistration,
        fields: dict[str, Any],
        models_by_name: dict[str, Any],
    ) -> ResolvedSearchField:
        parts = path.split(".")
        if len(parts) - 1 > DEFAULT_SEARCH_LIMITS.max_relation_depth:
            raise SearchPlanValidationError(
                f"Field path '{path}' exceeds the maximum relation depth"
            )

        root = fields.get(parts[0])
        if root is None:
            raise SearchPlanValidationError(
                f"Field '{parts[0]}' does not exist on model '{model_name}'"
            )
        root_config = _search_config(root)
        if _is_sensitive(root) or not (
            root_config.get("enabled") and root_config.get("filter")
        ):
            raise SearchPlanValidationError(f"Field '{parts[0]}' is not filterable")

        root_type = str(
            getattr(getattr(root, "type", ""), "value", getattr(root, "type", ""))
        )
        if len(parts) == 1 and root_type not in RELATION_FIELD_TYPES:
            return ResolvedSearchField(
                path,
                model_name,
                root,
                registration,
                selection_values=_selection_values(models_by_name[model_name], root),
            )

        if root_type not in RELATION_FIELD_TYPES:
            raise SearchPlanValidationError(f"Field '{parts[0]}' is not a relation")

        related_model_name = _related_model_name(registration, parts[0])
        if related_model_name is None:
            raise SearchPlanValidationError(
                f"Relation '{parts[0]}' has no registered authorization policy"
            )
        related_registration = require_search_model_registration(related_model_name)
        if len(parts) == 1:
            return ResolvedSearchField(
                path=path,
                model_name=model_name,
                field=root,
                registration=registration,
                related_model_name=related_model_name,
                related_registration=related_registration,
                selection_values=_selection_values(models_by_name[model_name], root),
            )

        if parts[1] not in (root_config.get("relation_fields") or []):
            raise SearchPlanValidationError(
                f"Related field '{path}' is not explicitly allowed"
            )

        related_model = models_by_name.get(related_model_name)
        if related_model is None:
            raise SearchPlanValidationError(
                f"Related model '{related_model_name}' has no persisted metadata"
            )
        terminal = _field_map(related_model).get(parts[1])
        terminal_config = _search_config(terminal) if terminal is not None else {}
        if (
            terminal is None
            or _is_sensitive(terminal)
            or not (terminal_config.get("enabled") and terminal_config.get("filter"))
        ):
            raise SearchPlanValidationError(f"Related field '{path}' is not filterable")
        return ResolvedSearchField(
            path=path,
            model_name=model_name,
            field=terminal,
            registration=registration,
            related_model_name=related_model_name,
            related_registration=related_registration,
            selection_values=_selection_values(related_model, terminal),
        )
