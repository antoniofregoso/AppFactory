from __future__ import annotations

import json
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)
from app.domains.system.search.limits import DEFAULT_SEARCH_LIMITS

MAX_FILTERS_PER_QUERY = DEFAULT_SEARCH_LIMITS.max_filters_per_query
MAX_ORDERS_PER_QUERY = DEFAULT_SEARCH_LIMITS.max_orders_per_query
MAX_QUERIES_PER_PLAN = DEFAULT_SEARCH_LIMITS.max_models_per_plan
MAX_RESULTS_PER_QUERY = DEFAULT_SEARCH_LIMITS.max_results_per_query
MAX_STRING_LENGTH = DEFAULT_SEARCH_LIMITS.max_string_length


class SearchOperator(str, Enum):
    EQ = "eq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    BEFORE = "before"
    AFTER = "after"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS_ANY = "contains_any"
    CONTAINS_ALL = "contains_all"
    BETWEEN = "between"
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"


class SearchOrderDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


JsonScalar = StrictStr | StrictBool | StrictInt | StrictFloat | None
FilterValue = JsonScalar | list[JsonScalar]

SCALAR_OPERATORS = {
    SearchOperator.EQ,
    SearchOperator.GT,
    SearchOperator.GTE,
    SearchOperator.LT,
    SearchOperator.LTE,
    SearchOperator.BEFORE,
    SearchOperator.AFTER,
    SearchOperator.CONTAINS,
    SearchOperator.STARTS_WITH,
}
LIST_OPERATORS = {
    SearchOperator.IN,
    SearchOperator.NOT_IN,
    SearchOperator.CONTAINS_ANY,
    SearchOperator.CONTAINS_ALL,
}
RELATIVE_DATE_OPERATORS = {
    SearchOperator.TODAY,
    SearchOperator.THIS_WEEK,
    SearchOperator.THIS_MONTH,
}


class SearchContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SearchFilter(SearchContractModel):
    field: Annotated[StrictStr, Field(min_length=1, max_length=255)]
    operator: SearchOperator
    value: FilterValue

    @model_validator(mode="after")
    def validate_value_shape(self) -> SearchFilter:
        value = self.value

        if self.operator in SCALAR_OPERATORS:
            if value is None or isinstance(value, list):
                raise ValueError(f"{self.operator.value} requires a non-null scalar")
        elif self.operator in LIST_OPERATORS:
            if (
                not isinstance(value, list)
                or not 1 <= len(value) <= DEFAULT_SEARCH_LIMITS.max_values_per_filter
            ):
                raise ValueError(
                    f"{self.operator.value} requires between 1 and "
                    f"{DEFAULT_SEARCH_LIMITS.max_values_per_filter} values"
                )
            if any(item is None for item in value):
                raise ValueError(f"{self.operator.value} does not accept null values")
            serialized = [
                json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value
            ]
            if len(serialized) != len(set(serialized)):
                raise ValueError(f"{self.operator.value} requires unique values")
        elif self.operator == SearchOperator.BETWEEN:
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("between requires exactly two values")
            if any(item is None for item in value):
                raise ValueError("between does not accept null values")
            start, end = value
            if (
                isinstance(start, (int, float))
                and not isinstance(start, bool)
                and isinstance(end, (int, float))
                and not isinstance(end, bool)
                and start > end
            ):
                raise ValueError("between start must not be greater than end")
        elif self.operator in RELATIVE_DATE_OPERATORS and value is not None:
            raise ValueError(f"{self.operator.value} requires a null value")

        values = value if isinstance(value, list) else [value]
        if any(
            isinstance(item, str) and len(item) > MAX_STRING_LENGTH for item in values
        ):
            raise ValueError(
                f"filter strings must not exceed {MAX_STRING_LENGTH} characters"
            )
        return self


class FilterGroup(SearchContractModel):
    and_filters: Annotated[
        list[SearchFilter] | None,
        Field(alias="and", max_length=MAX_FILTERS_PER_QUERY),
    ] = None
    or_filters: Annotated[
        list[SearchFilter] | None,
        Field(alias="or", max_length=MAX_FILTERS_PER_QUERY),
    ] = None

    @model_validator(mode="after")
    def require_one_logical_operator(self) -> FilterGroup:
        if (self.and_filters is None) == (self.or_filters is None):
            raise ValueError("filters must contain exactly one of 'and' or 'or'")
        return self

    @classmethod
    def empty_and(cls) -> FilterGroup:
        return cls.model_validate({"and": []})


class SearchOrder(SearchContractModel):
    field: Annotated[StrictStr, Field(min_length=1, max_length=255)]
    direction: SearchOrderDirection = SearchOrderDirection.ASC


class ModelSearchQuery(SearchContractModel):
    model: Annotated[StrictStr, Field(min_length=1, max_length=255)]
    text: Annotated[StrictStr, Field(max_length=MAX_STRING_LENGTH)] | None = None
    filters: FilterGroup = Field(default_factory=FilterGroup.empty_and)
    order: Annotated[list[SearchOrder], Field(max_length=MAX_ORDERS_PER_QUERY)] = Field(
        default_factory=list
    )
    limit: Annotated[StrictInt, Field(ge=1, le=MAX_RESULTS_PER_QUERY)] = (
        MAX_RESULTS_PER_QUERY
    )


class SearchPlanV1(SearchContractModel):
    version: Literal[1]
    intent: Literal["search_records"]
    queries: Annotated[list[ModelSearchQuery], Field(max_length=MAX_QUERIES_PER_PLAN)]
    needs_clarification: StrictBool
    clarification_question: (
        Annotated[StrictStr, Field(min_length=1, max_length=MAX_STRING_LENGTH)] | None
    )

    @model_validator(mode="after")
    def validate_clarification_state(self) -> SearchPlanV1:
        if self.needs_clarification:
            if self.queries:
                raise ValueError("clarification plans must not contain queries")
            if self.clarification_question is None:
                raise ValueError("clarification plans require a question")
        else:
            if not self.queries:
                raise ValueError("search plans require between 1 and 5 queries")
            if self.clarification_question is not None:
                raise ValueError(
                    "search plans must not contain a clarification question"
                )
        return self
