from datetime import datetime, timezone

import pytest

from app.domains.system.search.contracts import SearchOperator
from app.domains.system.search.temporal import (
    SearchTimezoneError,
    relative_date_bounds_utc,
    resolve_timezone,
)


def test_today_uses_local_midnight_and_converts_bounds_to_utc():
    start, end = relative_date_bounds_utc(
        SearchOperator.TODAY,
        "America/Mexico_City",
        datetime(2026, 7, 13, 18, 0, tzinfo=timezone.utc),
    )

    assert start == datetime(2026, 7, 13, 6, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 7, 14, 6, 0, tzinfo=timezone.utc)


def test_this_week_uses_iso_monday_and_month_handles_year_boundary():
    week_start, week_end = relative_date_bounds_utc(
        SearchOperator.THIS_WEEK,
        "UTC",
        datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc),
    )
    month_start, month_end = relative_date_bounds_utc(
        SearchOperator.THIS_MONTH,
        "UTC",
        datetime(2026, 12, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert week_start == datetime(2026, 7, 13, tzinfo=timezone.utc)
    assert week_end == datetime(2026, 7, 20, tzinfo=timezone.utc)
    assert month_start == datetime(2026, 12, 1, tzinfo=timezone.utc)
    assert month_end == datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_dst_transition_uses_each_boundary_offset_independently():
    start, end = relative_date_bounds_utc(
        SearchOperator.TODAY,
        "America/New_York",
        datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert start == datetime(2026, 3, 8, 5, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 3, 9, 4, 0, tzinfo=timezone.utc)


def test_invalid_iana_timezone_and_naive_reference_are_rejected():
    with pytest.raises(SearchTimezoneError, match="valid IANA"):
        resolve_timezone("Mexico/Not_A_Zone")
    with pytest.raises(SearchTimezoneError, match="include an offset"):
        relative_date_bounds_utc(
            SearchOperator.TODAY,
            "UTC",
            datetime(2026, 7, 13, 12, 0),
        )
