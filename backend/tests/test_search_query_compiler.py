from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.dialects import postgresql

from app.domains.system.search.authorization import SearchAuthorizationPolicy
from app.domains.system.search.compiler import SearchQueryCompiler
from app.domains.system.search.registry import SearchModelRegistration
from app.domains.system.search.validator import SearchPlanValidator
from app.domains.users.models.user_user import UserUser
from tests.test_search_plan_validator import field, models, plan


class TrackingRelatedPolicy(SearchAuthorizationPolicy):
    def __init__(self):
        self.user_ids = []

    def apply(self, statement, current_user_id):
        self.user_ids.append(current_user_id)
        return statement.where(UserUser.active.is_(True))

    def allows_record(self, record, current_user_id):
        return True


def _compiled(statement):
    return statement.compile(dialect=postgresql.dialect())


def test_related_filter_uses_exists_and_applies_related_authorization_policy():
    validated = SearchPlanValidator.validate_with_models(
        plan(
            filters=[
                {
                    "field": "user_id.name",
                    "operator": "contains",
                    "value": "Antonio%_",
                }
            ]
        ),
        models(),
    ).queries[0]
    policy = TrackingRelatedPolicy()
    resolved = validated.filters[0].resolved_field
    secured_registration = SearchModelRegistration(
        orm_class=UserUser,
        authorization_policy=policy,
        url_builder=lambda record_uuid: str(record_uuid),
    )
    secured_filter = replace(
        validated.filters[0],
        resolved_field=replace(
            resolved,
            related_registration=secured_registration,
        ),
    )
    secured_query = replace(validated, filters=(secured_filter,))

    compiled = _compiled(SearchQueryCompiler.compile(secured_query, 7))
    sql = str(compiled)

    assert policy.user_ids == [7]
    assert "EXISTS" in sql
    assert "user_user.active IS true" in sql
    assert "system_tasks.user_id" in sql
    assert "Antonio" not in sql
    assert "%Antonio\\%\\_%" in compiled.params.values()


def test_root_and_related_values_remain_bound_parameters():
    record_uuid = "12345678-1234-5678-1234-567812345678"
    validated = SearchPlanValidator.validate_with_models(
        plan(
            filters=[
                {"field": "priority", "operator": "eq", "value": "Urgent"},
                {"field": "user_id", "operator": "eq", "value": record_uuid},
            ],
            order=[{"field": "title", "direction": "asc"}],
        ),
        models(),
    ).queries[0]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    assert "Urgent" not in sql
    assert record_uuid not in sql
    assert "EXISTS" in sql
    assert "ORDER BY" in sql
    assert "system_tasks.uuid ASC" in sql
    assert "Urgent" in compiled.params.values()


def test_many_to_many_contains_all_uses_one_authorized_exists_per_value():
    user_one = "12345678-1234-5678-1234-567812345678"
    user_two = "87654321-4321-8765-4321-876543218765"
    metadata = models()
    metadata.append(
        SimpleNamespace(
            name="system.message",
            search=True,
            fields=[
                SimpleNamespace(
                    name="to_users",
                    type="many2many_pills",
                    search_config={
                        "enabled": True,
                        "filter": True,
                        "operators": ["contains_any", "contains_all"],
                    },
                )
            ],
        )
    )
    validated = SearchPlanValidator.validate_with_models(
        plan(
            filters=[
                {
                    "field": "to_users",
                    "operator": "contains_all",
                    "value": [user_one, user_two],
                }
            ],
            model="system.message",
        ),
        metadata,
    ).queries[0]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    # One EXISTS belongs to message visibility; two enforce both recipients.
    assert sql.count("EXISTS") == 3
    assert "system_message_user_rel" in sql
    assert user_one not in sql
    assert user_two not in sql


def test_localized_selection_and_relative_date_compile_to_bound_values():
    validated = SearchPlanValidator.validate_with_models(
        plan(
            filters=[
                {"field": "priority", "operator": "eq", "value": "Urgente"},
                {
                    "field": "date_due",
                    "operator": "this_week",
                    "value": None,
                },
            ]
        ),
        models(),
        language="es",
    ).queries[0]

    compiled = _compiled(
        SearchQueryCompiler.compile(
            validated,
            7,
            language="es",
            timezone_name="America/Mexico_City",
            now=datetime(2026, 7, 15, 18, 0, tzinfo=timezone.utc),
        )
    )
    sql = str(compiled)

    assert "Urgente" not in sql
    assert "Urgent" not in sql
    assert "Urgent" in compiled.params.values()
    assert datetime(2026, 7, 13, 6, 0, tzinfo=timezone.utc) in compiled.params.values()
    assert datetime(2026, 7, 20, 6, 0, tzinfo=timezone.utc) in compiled.params.values()


def test_free_text_query_compiles_to_ranked_fts_match():
    validated = SearchPlanValidator.validate_with_models(
        plan(text="urgent report"),
        models(),
    ).queries[0]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    assert "to_tsvector" in sql
    assert "plainto_tsquery" in sql
    assert "@@" in sql
    assert "ts_rank" in sql
    assert "ORDER BY" in sql
    assert sql.index("ts_rank") < sql.index("system_tasks.uuid ASC")
    # The query text is bound, not inlined.
    assert "urgent report" not in sql
    assert "urgent report" in compiled.params.values()


def test_free_text_field_weight_defaults_to_d_and_honors_configured_weight():
    metadata = models()
    metadata[0].fields.append(
        field("status", "string", enabled=True, text=True, weight="A")
    )
    validated = SearchPlanValidator.validate_with_models(
        plan(text="urgent"),
        metadata,
    ).queries[0]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    # `title` has no configured weight in the shared `models()` fixture and
    # falls back to 'D'; the appended `status` field is explicitly 'A'. The
    # weight label is a literal (not a bound param — see `_fts_field_vector`),
    # so it's asserted directly in the compiled SQL text.
    assert "setweight(to_tsvector(%(to_tsvector_1)s, coalesce(CAST" in sql
    assert "), 'D')" in sql
    assert "), 'A')" in sql


def test_free_text_predicate_ors_across_text_fields():
    metadata = models()
    metadata[0].fields.append(
        field("status", "string", enabled=True, text=True, weight="B")
    )
    validated = SearchPlanValidator.validate_with_models(
        plan(text="urgent"),
        metadata,
    ).queries[0]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    # One `@@` use per field (WHERE) and one `ts_rank` use per field (ORDER BY).
    assert sql.count("plainto_tsquery(") == len(validated.text_fields) * 2
    assert " OR " in sql


def test_html_field_is_included_and_strips_tags_in_fts_vector():
    metadata = models()
    description = next(f for f in metadata[0].fields if f.name == "description")
    assert description.type == "html"
    description.search_config = {"enabled": True, "text": True, "weight": "C"}

    validated = SearchPlanValidator.validate_with_models(
        plan(text="urgent"),
        metadata,
    ).queries[0]

    # The html exclusion is gone: an enabled+text html field is now resolved.
    assert any(f.field.name == "description" for f in validated.text_fields)

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    assert "regexp_replace" in sql
    assert "<[^>]*>" in compiled.params.values()


def test_non_html_field_does_not_get_regexp_replace():
    validated = SearchPlanValidator.validate_with_models(
        plan(text="urgent"),
        models(),
    ).queries[0]

    # `models()`'s only enabled+text field is `title` (type "string").
    assert [f.field.name for f in validated.text_fields] == ["title"]

    compiled = _compiled(SearchQueryCompiler.compile(validated, 7))
    sql = str(compiled)

    assert "regexp_replace" not in sql
