import json

import pytest

from app.domains.system.search.interpreter import (
    OpenAIResponsesSearchInterpreter,
    SearchContext,
    SearchInterpreterInvalidPlan,
)
from app.domains.system.search.schema import SearchSchemaService
from tests.test_search_plan_validator import models


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": self.text}],
                }
            ]
        }


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def valid_plan():
    return {
        "version": 1,
        "intent": "search_records",
        "queries": [
            {
                "model": "system.task",
                "text": "reporte",
                "filters": {"and": []},
                "order": [],
                "limit": 20,
            }
        ],
        "needs_clarification": False,
        "clarification_question": None,
    }


@pytest.mark.asyncio
async def test_openai_adapter_requests_strict_search_plan_json_schema():
    client = FakeClient(FakeResponse(json.dumps(valid_plan())))
    interpreter = OpenAIResponsesSearchInterpreter(
        api_key="test-secret",
        model="test-model",
        client=client,
    )
    schema = SearchSchemaService.build_with_models(
        models(), language="es", timezone_name="America/Mexico_City"
    )

    plan = await interpreter.interpret(
        "tareas con reporte",
        schema,
        SearchContext(language="es", timezone="America/Mexico_City"),
    )

    assert plan.queries[0].model == "system.task"
    _, request = client.calls[0]
    assert request["json"]["text"]["format"]["type"] == "json_schema"
    assert request["json"]["text"]["format"]["strict"] is True
    plan_schema = request["json"]["text"]["format"]["schema"]
    query_schema = plan_schema["$defs"]["ModelSearchQuery"]
    assert set(query_schema["required"]) == set(query_schema["properties"])
    assert "default" not in json.dumps(plan_schema)
    assert request["headers"]["Authorization"] == "Bearer test-secret"
    serialized_input = request["json"]["input"][1]["content"][0]["text"]
    assert "password" not in serialized_input


@pytest.mark.asyncio
async def test_openai_adapter_rejects_non_contract_output():
    interpreter = OpenAIResponsesSearchInterpreter(
        api_key="test-secret",
        model="test-model",
        client=FakeClient(FakeResponse('{"sql":"DROP TABLE users"}')),
    )
    schema = SearchSchemaService.build_with_models(
        models(), language="en", timezone_name="UTC"
    )

    with pytest.raises(SearchInterpreterInvalidPlan):
        await interpreter.interpret(
            "all users",
            schema,
            SearchContext(language="en", timezone="UTC"),
        )
