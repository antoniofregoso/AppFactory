from dataclasses import dataclass


@dataclass(frozen=True)
class SearchLimits:
    max_models_per_plan: int = 5
    max_filters_per_query: int = 10
    max_orders_per_query: int = 3
    max_values_per_filter: int = 20
    max_relation_depth: int = 1
    max_results_per_query: int = 20
    max_results_total: int = 50
    max_string_length: int = 500

    def allocate_results(self, requested_limits: list[int]) -> tuple[int, ...]:
        remaining = self.max_results_total
        allocated = []
        for requested in requested_limits:
            amount = min(max(0, requested), self.max_results_per_query, remaining)
            allocated.append(amount)
            remaining -= amount
        return tuple(allocated)


DEFAULT_SEARCH_LIMITS = SearchLimits()
