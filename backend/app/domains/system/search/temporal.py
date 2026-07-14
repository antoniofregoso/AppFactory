from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config.settings import settings
from app.domains.system.search.contracts import SearchOperator


class SearchTimezoneError(ValueError):
    pass


def resolve_timezone(timezone_name: str | None = None) -> ZoneInfo:
    configured = timezone_name or settings.DEFAULT_TIMEZONE or "UTC"
    try:
        return ZoneInfo(configured)
    except ZoneInfoNotFoundError as exc:
        raise SearchTimezoneError(
            f"Timezone '{configured}' is not a valid IANA identifier"
        ) from exc


def relative_date_bounds_utc(
    operator: SearchOperator,
    timezone_name: str | None = None,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    zone = resolve_timezone(timezone_name)
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise SearchTimezoneError("The reference datetime must include an offset")
    local_date = instant.astimezone(zone).date()

    if operator == SearchOperator.TODAY:
        start_date = local_date
        end_date = start_date + timedelta(days=1)
    elif operator == SearchOperator.THIS_WEEK:
        start_date = local_date - timedelta(days=local_date.weekday())
        end_date = start_date + timedelta(days=7)
    elif operator == SearchOperator.THIS_MONTH:
        start_date = local_date.replace(day=1)
        end_date = (
            date(start_date.year + 1, 1, 1)
            if start_date.month == 12
            else date(start_date.year, start_date.month + 1, 1)
        )
    else:
        raise ValueError(f"Operator '{operator.value}' is not a relative date")

    local_start = datetime.combine(start_date, time.min, tzinfo=zone)
    local_end = datetime.combine(end_date, time.min, tzinfo=zone)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)
