from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import JSON, and_, func, inspect, literal_column, or_, select

from app.domains.system.search.contracts import SearchOperator
from app.domains.system.search.registry import require_search_model_registration
from app.domains.system.search.temporal import relative_date_bounds_utc
from app.domains.system.search.validator import (
    RELATION_FIELD_TYPES,
    ResolvedSearchField,
    ValidatedModelSearchQuery,
    ValidatedSearchFilter,
)


class SearchQueryCompilationError(ValueError):
    pass


def _relationship_for(resolved: ResolvedSearchField):
    field_name = resolved.path.split(".", 1)[0]
    mapper = inspect(resolved.registration.orm_class)
    names = [field_name]
    if field_name.endswith("_id"):
        names.append(field_name[:-3])
    relationship = next(
        (mapper.relationships[name] for name in names if name in mapper.relationships),
        None,
    )
    if relationship is None:
        raise SearchQueryCompilationError(
            f"Relationship for field '{field_name}' cannot be compiled"
        )
    return relationship


def _localized_column(column: Any, language: str) -> Any:
    try:
        column_type = column.property.columns[0].type
    except (AttributeError, IndexError):
        return column
    if not isinstance(column_type, JSON):
        return column

    locale = "es_MX" if language.startswith("es") else "en_US"
    candidates = [locale, language, "en_US", "en", "es_MX", "es"]
    unique_candidates = list(dict.fromkeys(candidates))
    return func.coalesce(*(column[key].as_string() for key in unique_candidates))


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


_FTS_WEIGHTS = {"A", "B", "C", "D"}


_HTML_TAG_PATTERN = "<[^>]*>"


def _fts_source_text(column: Any, field_type: str) -> Any:
    try:
        column_type = column.property.columns[0].type
    except (AttributeError, IndexError):
        column_type = None

    if isinstance(column_type, JSON):
        # Both locales are folded into one vector (language-independent
        # matching) instead of picking one via COALESCE like
        # `_localized_column` does, so a single index covers a field
        # regardless of the request/document language.
        source = (
            func.coalesce(column["es_MX"].as_string(), "")
            + " "
            + func.coalesce(column["en_US"].as_string(), "")
        )
    else:
        source = func.coalesce(column, "")

    if field_type == "html":
        # Deliberately simple tag stripping (no entity decoding, no
        # <script>/<style> content removal) — content comes from the app's
        # allowlisted Quill editor, not arbitrary raw HTML. Matches the
        # equivalent GIN index expression exactly (see the FTS HTML indexes
        # migration) so PostgreSQL can use it.
        source = func.regexp_replace(source, _HTML_TAG_PATTERN, " ", "g")
    return source


def _fts_field_vector(model_class: Any, resolved: ResolvedSearchField) -> Any:
    column = getattr(model_class, resolved.field.name)
    source = _fts_source_text(column, resolved.field_type)
    weight = str((resolved.field.search_config or {}).get("weight") or "D").upper()
    if weight not in _FTS_WEIGHTS:
        weight = "D"
    # `setweight`'s second argument is PostgreSQL's internal `"char"` type, not
    # VARCHAR/TEXT — asyncpg's prepared-statement protocol has no implicit
    # cast for a bound VARCHAR parameter into it, so the (whitelisted-above)
    # label is embedded as a literal instead of a bound parameter.
    return func.setweight(func.to_tsvector("simple", source), literal_column(f"'{weight}'"))


def _typed_value(field_type: str, value: Any) -> Any:
    if value is None:
        return None
    if field_type == "integer":
        return int(value)
    if field_type in {"decimal", "monetary", "percentage"}:
        return Decimal(value)
    if field_type == "date":
        return date.fromisoformat(value)
    if field_type == "datetime":
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if field_type in RELATION_FIELD_TYPES:
        return UUID(value)
    return value


def _column_predicate(
    column: Any,
    operator: SearchOperator,
    value: Any,
    field_type: str,
    timezone_name: str | None = None,
    now: datetime | None = None,
) -> Any:
    if operator in {
        SearchOperator.TODAY,
        SearchOperator.THIS_WEEK,
        SearchOperator.THIS_MONTH,
    }:
        start, end = relative_date_bounds_utc(operator, timezone_name, now)
        if field_type == "date":
            return and_(column >= start.date(), column < end.date())
        return and_(column >= start, column < end)

    values: Iterable[Any] = value if isinstance(value, list) else [value]
    typed_values = [_typed_value(field_type, item) for item in values]

    if operator == SearchOperator.EQ:
        return column == typed_values[0]
    if operator == SearchOperator.IN:
        return column.in_(typed_values)
    if operator == SearchOperator.NOT_IN:
        return column.not_in(typed_values)
    if operator == SearchOperator.GT:
        return column > typed_values[0]
    if operator == SearchOperator.GTE:
        return column >= typed_values[0]
    if operator == SearchOperator.LT:
        return column < typed_values[0]
    if operator == SearchOperator.LTE:
        return column <= typed_values[0]
    if operator == SearchOperator.BEFORE:
        return column < typed_values[0]
    if operator == SearchOperator.AFTER:
        return column > typed_values[0]
    if operator == SearchOperator.BETWEEN:
        return column.between(typed_values[0], typed_values[1])
    if operator == SearchOperator.CONTAINS:
        escaped = _escape_like(str(typed_values[0]))
        return column.ilike(f"%{escaped}%", escape="\\")
    if operator == SearchOperator.STARTS_WITH:
        escaped = _escape_like(str(typed_values[0]))
        return column.ilike(f"{escaped}%", escape="\\")
    raise SearchQueryCompilationError(
        f"Operator '{operator.value}' is not implemented by the query compiler"
    )


def _related_select(
    resolved: ResolvedSearchField,
    current_user_id: int,
) -> tuple[Any, Any]:
    relationship = _relationship_for(resolved)
    registration = resolved.related_registration
    if registration is None:
        raise SearchQueryCompilationError(
            f"Relation '{resolved.path}' has no authorization policy"
        )

    related_class = registration.orm_class
    if relationship.secondary is None:
        statement = select(1).select_from(related_class).where(relationship.primaryjoin)
    else:
        related_from = relationship.secondary.join(
            inspect(related_class).local_table,
            relationship.secondaryjoin,
        )
        statement = select(1).select_from(related_from).where(relationship.primaryjoin)

    statement = registration.authorization_policy.apply(statement, current_user_id)
    return statement, related_class


def _relation_predicate(
    validated_filter: ValidatedSearchFilter,
    current_user_id: int,
    language: str,
    timezone_name: str | None,
    now: datetime | None,
) -> Any:
    search_filter = validated_filter.filter
    resolved = validated_filter.resolved_field
    parts = resolved.path.split(".", 1)

    if len(parts) == 2:
        statement, related_class = _related_select(resolved, current_user_id)
        column = _localized_column(
            getattr(related_class, resolved.field.name), language
        )
        predicate = _column_predicate(
            column,
            search_filter.operator,
            validated_filter.value,
            resolved.field_type,
            timezone_name,
            now,
        )
        return statement.where(predicate).exists()

    values = (
        validated_filter.value
        if isinstance(validated_filter.value, list)
        else [validated_filter.value]
    )

    def related_uuid_predicate(column, items):
        return column.in_([_typed_value(resolved.field_type, item) for item in items])

    if search_filter.operator == SearchOperator.CONTAINS_ALL:
        predicates = []
        for item in values:
            statement, related_class = _related_select(resolved, current_user_id)
            predicates.append(
                statement.where(
                    related_uuid_predicate(related_class.uuid, [item])
                ).exists()
            )
        return and_(*predicates)

    statement, related_class = _related_select(resolved, current_user_id)
    if search_filter.operator in {
        SearchOperator.EQ,
        SearchOperator.IN,
        SearchOperator.CONTAINS_ANY,
    }:
        return statement.where(
            related_uuid_predicate(related_class.uuid, values)
        ).exists()
    raise SearchQueryCompilationError(
        f"Operator '{search_filter.operator.value}' cannot filter relation "
        f"'{resolved.path}'"
    )


class SearchQueryCompiler:
    @staticmethod
    def compile(
        validated_query: ValidatedModelSearchQuery,
        current_user_id: int,
        language: str = "es",
        timezone_name: str | None = None,
        now: datetime | None = None,
    ) -> Any:
        registration = require_search_model_registration(validated_query.query.model)

        model_class = registration.orm_class
        statement = registration.authorization_policy.apply(
            select(model_class), current_user_id
        )

        predicates = []
        rank_expression = None
        if validated_query.query.text:
            tsquery = func.plainto_tsquery("simple", validated_query.query.text)
            field_vectors = [
                _fts_field_vector(model_class, resolved)
                for resolved in validated_query.text_fields
            ]
            predicates.append(or_(*(v.op("@@")(tsquery) for v in field_vectors)))
            rank_terms = [func.ts_rank(v, tsquery) for v in field_vectors]
            rank_expression = rank_terms[0]
            for term in rank_terms[1:]:
                rank_expression = rank_expression + term
        for validated_filter in validated_query.filters:
            resolved = validated_filter.resolved_field
            if resolved.related_registration is not None:
                predicates.append(
                    _relation_predicate(
                        validated_filter,
                        current_user_id,
                        language,
                        timezone_name,
                        now,
                    )
                )
                continue
            column = _localized_column(
                getattr(model_class, resolved.field.name), language
            )
            predicates.append(
                _column_predicate(
                    column,
                    validated_filter.filter.operator,
                    validated_filter.value,
                    resolved.field_type,
                    timezone_name,
                    now,
                )
            )

        if predicates:
            combine = (
                or_ if validated_query.query.filters.or_filters is not None else and_
            )
            statement = statement.where(combine(*predicates))

        for validated_order in validated_query.orders:
            resolved = validated_order.resolved_field
            if resolved.related_registration is not None:
                raise SearchQueryCompilationError(
                    f"Ordering by related field '{resolved.path}' is not supported"
                )
            column = _localized_column(
                getattr(model_class, resolved.field.name), language
            )
            direction = validated_order.order.direction.value
            statement = statement.order_by(
                column.desc() if direction == "desc" else column.asc()
            )

        if rank_expression is not None:
            statement = statement.order_by(rank_expression.desc())
        statement = statement.order_by(model_class.uuid.asc())
        return statement.limit(validated_query.result_limit)
