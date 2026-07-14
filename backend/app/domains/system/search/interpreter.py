from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config.settings import settings
from app.domains.system.search.contracts import SearchPlanV1
from app.domains.system.search.schema import SearchableSchemaV1


def _strict_json_schema(value):
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    strict = {
        key: _strict_json_schema(item)
        for key, item in value.items()
        if key != "default"
    }
    properties = strict.get("properties")
    if isinstance(properties, dict):
        strict["required"] = list(properties)
        strict["additionalProperties"] = False
    return strict


class SearchInterpreterError(RuntimeError):
    pass


class SearchInterpreterUnavailable(SearchInterpreterError):
    pass


class SearchInterpreterInvalidPlan(SearchInterpreterError):
    pass


@dataclass(frozen=True)
class SearchContext:
    language: str
    timezone: str
    original_query: str | None = None
    clarification_answer: str | None = None


class SearchInterpreter(Protocol):
    async def interpret(
        self,
        query: str,
        searchable_schema: SearchableSchemaV1,
        context: SearchContext,
    ) -> SearchPlanV1: ...


class OpenAIResponsesSearchInterpreter:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def interpret(
        self,
        query: str,
        searchable_schema: SearchableSchemaV1,
        context: SearchContext,
    ) -> SearchPlanV1:
        user_payload = {
            "query": query,
            "original_query": context.original_query,
            "clarification_answer": context.clarification_answer,
            "searchable_schema": searchable_schema.model_dump(mode="json"),
        }
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Convert the user's request into SearchPlanV1. Use only "
                                "models, fields, operators, and selection values present in "
                                "searchable_schema. Never emit SQL. If required information "
                                "is ambiguous, return a clarification plan with no queries."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(user_payload, ensure_ascii=False),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "search_plan_v1",
                    "strict": True,
                    "schema": _strict_json_schema(
                        SearchPlanV1.model_json_schema(by_alias=True)
                    ),
                }
            },
        }
        try:
            if self.client is not None:
                response = await self.client.post(
                    f"{self.base_url}/responses",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/responses",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload,
                        timeout=self.timeout_seconds,
                    )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError("AI search interpretation timed out") from exc
        except httpx.HTTPError as exc:
            raise SearchInterpreterUnavailable(
                "AI search provider is unavailable"
            ) from exc

        try:
            body = response.json()
            text = next(
                content["text"]
                for item in body.get("output", [])
                if item.get("type") == "message"
                for content in item.get("content", [])
                if content.get("type") == "output_text"
            )
            return SearchPlanV1.model_validate_json(text)
        except (KeyError, StopIteration, TypeError, ValueError) as exc:
            raise SearchInterpreterInvalidPlan(
                "AI provider returned an invalid SearchPlanV1"
            ) from exc


def get_search_interpreter() -> SearchInterpreter | None:
    provider = settings.SEARCH_AI_PROVIDER.strip().casefold()
    if not provider:
        return None
    if provider != "openai":
        raise SearchInterpreterUnavailable(
            f"Unsupported search AI provider '{settings.SEARCH_AI_PROVIDER}'"
        )
    api_key = settings.SEARCH_AI_API_KEY.get_secret_value()
    if not api_key or not settings.SEARCH_AI_MODEL:
        return None
    return OpenAIResponsesSearchInterpreter(
        api_key=api_key,
        model=settings.SEARCH_AI_MODEL,
        base_url=settings.SEARCH_AI_BASE_URL,
        timeout_seconds=settings.SEARCH_AI_TIMEOUT_SECONDS,
    )
