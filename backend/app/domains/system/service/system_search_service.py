import asyncio
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core.config.settings import settings
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.compiler import SearchQueryCompiler
from app.domains.system.search.contracts import ModelSearchQuery, SearchPlanV1
from app.domains.system.search.interpreter import (
    SearchContext,
    SearchInterpreterInvalidPlan,
    SearchInterpreterUnavailable,
    get_search_interpreter,
)
from app.domains.system.search.limits import DEFAULT_SEARCH_LIMITS
from app.domains.system.search.registry import require_search_model_registration
from app.domains.system.search.repository import SearchQueryRepository
from app.domains.system.search.schema import SearchableSchemaError, SearchSchemaService
from app.domains.system.search.validator import (
    SearchPlanValidationError,
    SearchPlanValidator,
)


def _localized(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        preferred = "es_MX" if lang == "es" else "en_US"
        return str(
            value.get(preferred)
            or value.get(lang)
            or value.get("en_US")
            or value.get("en")
            or value.get("es_MX")
            or value.get("es")
            or next(iter(value.values()), "")
        )
    return "" if value is None else str(value)


def _search_text(value: Any, lang: str) -> str:
    if isinstance(value, list):
        return " ".join(_search_text(item, lang) for item in value)
    if isinstance(value, dict) and "uuid" in value:
        return " ".join(str(value.get(key) or "") for key in ("name", "email"))
    return _localized(value, lang)


_HTML_TAG_RE = re.compile(r"<[^>]*>")


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", _HTML_TAG_RE.sub(" ", value)).strip()


def _field_type(field: Any) -> str:
    value = getattr(field, "type", "")
    return str(getattr(value, "value", value))


def _field_text(record: Any, field: Any, language: str) -> str:
    text = _search_text(getattr(record, field.name, None), language)
    return _strip_html(text) if _field_type(field) == "html" else text


@dataclass(frozen=True)
class SearchResult:
    model: str
    model_label: str
    uuid: str
    title: str
    subtitle: str | None
    snippet: str | None
    url: str
    score: int


class SearchResults(list[SearchResult]):
    def __init__(
        self, results: list[SearchResult], *, queried_models: list[str]
    ) -> None:
        super().__init__(results)
        self.queried_models = tuple(sorted(set(queried_models)))


class SearchMode(str, Enum):
    AUTO = "AUTO"
    TEXT = "TEXT"
    AI = "AI"


@dataclass(frozen=True)
class SearchIssue:
    code: str
    message: str
    model: str | None = None
    field: str | None = None


@dataclass(frozen=True)
class SearchExecution:
    status: str
    interpreted_query: str
    needs_clarification: bool
    clarification_question: str | None
    results: SearchResults
    errors: tuple[SearchIssue, ...] = ()


def _message(language: str, spanish: str, english: str) -> str:
    return spanish if language.startswith("es") else english


def _plan_summary(plan, models_by_name: dict[str, Any], language: str) -> str:
    parts = []
    for query in plan.queries:
        model = models_by_name.get(query.model)
        label = _localized(getattr(model, "label", {}), language) or query.model
        clauses = []
        if query.text:
            clauses.append(f'"{query.text}"')
        filters = query.filters.and_filters or query.filters.or_filters or []
        clauses.extend(
            f"{item.field} {item.operator.value} {item.value}" for item in filters
        )
        parts.append(f"{label}: {', '.join(clauses)}" if clauses else label)
    return " · ".join(parts)


class SystemSearchService:
    MAX_LIMIT = DEFAULT_SEARCH_LIMITS.max_results_total

    @staticmethod
    async def search(
        query: str, current_user_id: int, lang: str = "es", limit: int = 20
    ) -> SearchResults:
        async with asyncio.timeout(settings.SEARCH_TIMEOUT_SECONDS):
            return await SystemSearchService._search(
                query, current_user_id, lang, limit
            )

    @staticmethod
    async def run(
        query: str,
        current_user_id: int,
        *,
        lang: str = "es",
        limit: int = 20,
        mode: SearchMode | str = SearchMode.AUTO,
        model: str | None = None,
        original_query: str | None = None,
        clarification_answer: str | None = None,
        timezone_name: str | None = None,
    ) -> SearchExecution:
        normalized_mode = SearchMode(str(getattr(mode, "value", mode)).upper())
        timeout_seconds = settings.SEARCH_TIMEOUT_SECONDS
        if normalized_mode is not SearchMode.TEXT:
            timeout_seconds += settings.SEARCH_AI_TIMEOUT_SECONDS
        async with asyncio.timeout(timeout_seconds):
            return await SystemSearchService._run(
                query,
                current_user_id,
                lang=lang,
                limit=limit,
                mode=normalized_mode,
                model=model,
                original_query=original_query,
                clarification_answer=clarification_answer,
                timezone_name=timezone_name,
            )

    @staticmethod
    async def _run(
        query: str,
        current_user_id: int,
        *,
        lang: str,
        limit: int,
        mode: SearchMode | str,
        model: str | None,
        original_query: str | None,
        clarification_answer: str | None,
        timezone_name: str | None,
    ) -> SearchExecution:
        normalized_mode = SearchMode(str(getattr(mode, "value", mode)).upper())
        normalized_query = " ".join(str(query or "").split())[
            : DEFAULT_SEARCH_LIMITS.max_string_length
        ]
        if normalized_mode is SearchMode.TEXT:
            results = await SystemSearchService._search(
                normalized_query, current_user_id, lang, limit
            )
            return SearchExecution("OK", normalized_query, False, None, results)

        if bool(original_query) != bool(clarification_answer):
            raise SearchPlanValidationError(
                "original_query and clarification_answer must be provided together"
            )

        try:
            interpreter = get_search_interpreter()
        except SearchInterpreterUnavailable as exc:
            return await SystemSearchService._ai_failure(
                normalized_query,
                current_user_id,
                lang,
                limit,
                normalized_mode,
                "AI_UNAVAILABLE",
                str(exc),
            )
        if interpreter is None:
            return await SystemSearchService._ai_failure(
                normalized_query,
                current_user_id,
                lang,
                limit,
                normalized_mode,
                "AI_UNAVAILABLE",
                _message(
                    lang,
                    "La interpretación con IA no está configurada.",
                    "AI interpretation is not configured.",
                ),
            )

        models = list(await SystemModelRepository.get_all_with_fields())
        timezone_name = timezone_name or settings.DEFAULT_TIMEZONE
        try:
            schema = SearchSchemaService.build_with_models(
                models,
                language=lang,
                timezone_name=timezone_name,
                requested_model=model,
            )
            context = SearchContext(
                language=lang,
                timezone=timezone_name,
                original_query=original_query,
                clarification_answer=clarification_answer,
            )
            async with asyncio.timeout(settings.SEARCH_AI_TIMEOUT_SECONDS):
                plan = await interpreter.interpret(normalized_query, schema, context)
            exposed_models = {item.name for item in schema.models}
            if any(item.model not in exposed_models for item in plan.queries):
                raise SearchPlanValidationError(
                    "AI plan references a model outside the authorized schema"
                )
            validated = SearchPlanValidator.validate_with_models(plan, models, lang)
        except TimeoutError:
            return await SystemSearchService._ai_failure(
                normalized_query,
                current_user_id,
                lang,
                limit,
                normalized_mode,
                "TIMEOUT",
                _message(
                    lang,
                    "La interpretación con IA agotó el tiempo disponible.",
                    "AI interpretation timed out.",
                ),
            )
        except SearchInterpreterUnavailable as exc:
            return await SystemSearchService._ai_failure(
                normalized_query,
                current_user_id,
                lang,
                limit,
                normalized_mode,
                "AI_UNAVAILABLE",
                str(exc),
            )
        except (
            SearchInterpreterInvalidPlan,
            SearchPlanValidationError,
            SearchableSchemaError,
        ):
            return await SystemSearchService._ai_failure(
                normalized_query,
                current_user_id,
                lang,
                limit,
                normalized_mode,
                "INVALID_PLAN",
                _message(
                    lang,
                    "La IA devolvió un plan de búsqueda no válido.",
                    "The AI returned an invalid search plan.",
                ),
            )

        if plan.needs_clarification:
            return SearchExecution(
                status="NEEDS_CLARIFICATION",
                interpreted_query=normalized_query,
                needs_clarification=True,
                clarification_question=plan.clarification_question,
                results=SearchResults([], queried_models=[]),
            )

        models_by_name = {item.name: item for item in models}
        results = []
        issues = []
        queried_models = []
        for validated_query in validated.queries:
            model_name = validated_query.query.model
            queried_models.append(model_name)
            try:
                results.extend(
                    await SystemSearchService._execute_validated_query(
                        validated_query,
                        current_user_id,
                        lang,
                        models_by_name[model_name],
                        timezone_name=timezone_name,
                    )
                )
            except Exception:
                issues.append(
                    SearchIssue(
                        code="INTERNAL_ERROR",
                        message=_message(
                            lang,
                            "No se pudieron consultar algunos resultados.",
                            "Some results could not be queried.",
                        ),
                        model=model_name,
                    )
                )

        requested_limit = max(1, min(int(limit or 20), SystemSearchService.MAX_LIMIT))
        search_results = SearchResults(
            results[:requested_limit], queried_models=queried_models
        )
        return SearchExecution(
            status="PARTIAL" if issues else "OK",
            interpreted_query=_plan_summary(plan, models_by_name, lang),
            needs_clarification=False,
            clarification_question=None,
            results=search_results,
            errors=tuple(issues),
        )

    @staticmethod
    async def _ai_failure(
        query: str,
        current_user_id: int,
        lang: str,
        limit: int,
        mode: SearchMode,
        code: str,
        message: str,
    ) -> SearchExecution:
        issue = SearchIssue(code=code, message=message)
        if mode is SearchMode.AI:
            return SearchExecution(
                "FAILED",
                query,
                False,
                None,
                SearchResults([], queried_models=[]),
                (issue,),
            )
        results = await SystemSearchService._search(query, current_user_id, lang, limit)
        return SearchExecution("PARTIAL", query, False, None, results, (issue,))

    @staticmethod
    async def _execute_validated_query(
        validated_query: Any,
        current_user_id: int,
        lang: str,
        model: Any,
        timezone_name: str | None = None,
        terms: tuple[str, ...] | None = None,
    ) -> list[SearchResult]:
        statement = SearchQueryCompiler.compile(
            validated_query,
            current_user_id,
            language=lang,
            timezone_name=timezone_name,
        )
        records = await SearchQueryRepository.execute(statement)
        return SystemSearchService._map_plan_records(records, model, lang, terms)

    @staticmethod
    def _map_plan_records(
        records: list[Any],
        model: Any,
        language: str,
        terms: tuple[str, ...] | None = None,
    ) -> list[SearchResult]:
        searchable = [
            field
            for field in getattr(model, "fields", [])
            if isinstance(getattr(field, "search_config", None), dict)
            and field.search_config.get("enabled")
        ]
        title_field = next(
            (
                field
                for field in searchable
                if field.search_config.get("result") == "title"
            ),
            searchable[0] if searchable else None,
        )
        subtitle_fields = [
            field
            for field in searchable
            if field.search_config.get("result") == "subtitle"
        ]
        snippet_field = next(
            (
                field
                for field in searchable
                if field.search_config.get("result") == "snippet"
            ),
            None,
        )
        registration = require_search_model_registration(model.name)
        mapped = []
        for record in records:
            record_uuid = str(getattr(record, "uuid", ""))
            title = (
                _field_text(record, title_field, language)
                if title_field
                else record_uuid
            )
            subtitle = (
                " · ".join(
                    filter(
                        None,
                        (
                            _field_text(record, field, language)
                            for field in subtitle_fields
                        ),
                    )
                )
                or None
            )
            snippet = (
                _field_text(record, snippet_field, language)[:240]
                if snippet_field
                else None
            )
            score = 0
            if terms:
                title_folded = (title or "").casefold()
                score = sum(
                    (
                        100
                        if title_folded == term
                        else (
                            70
                            if title_folded.startswith(term)
                            else 50 if term in title_folded else 10
                        )
                    )
                    for term in terms
                )
            mapped.append(
                SearchResult(
                    model=model.name,
                    model_label=_localized(model.label, language),
                    uuid=record_uuid,
                    title=title or record_uuid,
                    subtitle=subtitle,
                    snippet=snippet,
                    url=registration.build_url(record_uuid),
                    score=score,
                )
            )
        return mapped

    @staticmethod
    async def _search(
        query: str, current_user_id: int, lang: str = "es", limit: int = 20
    ) -> SearchResults:
        normalized_query = " ".join(str(query or "").split())[
            : DEFAULT_SEARCH_LIMITS.max_string_length
        ]
        terms = tuple(
            term.casefold()
            for term in re.findall(r"[^\W_]+", normalized_query, flags=re.UNICODE)
        )
        if not terms:
            return SearchResults([], queried_models=[])

        requested_limit = max(1, min(int(limit or 20), SystemSearchService.MAX_LIMIT))
        models = [
            model
            for model in await SystemModelRepository.get_all_with_fields()
            if model.search
        ]

        queried_models: list[str] = []
        queries: list[ModelSearchQuery] = []
        for model in models:
            searchable = [
                field
                for field in model.fields
                if field.search_config.get("enabled")
                and field.search_config.get("text")
            ]
            if not searchable:
                continue
            queried_models.append(model.name)
            queries.append(
                ModelSearchQuery(
                    model=model.name,
                    text=normalized_query,
                    limit=DEFAULT_SEARCH_LIMITS.max_results_per_query,
                )
            )

        if not queries:
            return SearchResults([], queried_models=[])

        # Every enabled+text-searchable model is registered by construction (see
        # `queried_models` above), so this only ever raises for a programming error.
        plan = SearchPlanV1(
            version=1,
            intent="search_records",
            queries=queries,
            needs_clarification=False,
            clarification_question=None,
        )
        validated = SearchPlanValidator.validate_with_models(plan, models, lang)

        models_by_name = {model.name: model for model in models}
        results: list[SearchResult] = []
        for validated_query in validated.queries:
            results.extend(
                await SystemSearchService._execute_validated_query(
                    validated_query,
                    current_user_id,
                    lang,
                    models_by_name[validated_query.query.model],
                    terms=terms,
                )
            )

        return SearchResults(
            sorted(
                results,
                key=lambda item: (
                    -item.score,
                    item.model_label.casefold(),
                    item.title.casefold(),
                    item.uuid,
                ),
            )[:requested_limit],
            queried_models=queried_models,
        )
