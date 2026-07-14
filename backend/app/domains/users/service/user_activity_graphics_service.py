from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config.settings import settings
from app.domains.users.models.user_log import UserLog, UserLogStatus
from app.domains.users.repository.user_log_repository import UserLogRepository

PERIODS = {"today", "weekly", "monthly", "yearly", "annual"}
DAY_NAMES = (
    {"en": "Mon", "es": "Lun"},
    {"en": "Tue", "es": "Mar"},
    {"en": "Wed", "es": "Mié"},
    {"en": "Thu", "es": "Jue"},
    {"en": "Fri", "es": "Vie"},
    {"en": "Sat", "es": "Sáb"},
    {"en": "Sun", "es": "Dom"},
)
MONTH_NAMES = (
    {"en": "Jan", "es": "Ene"},
    {"en": "Feb", "es": "Feb"},
    {"en": "Mar", "es": "Mar"},
    {"en": "Apr", "es": "Abr"},
    {"en": "May", "es": "May"},
    {"en": "Jun", "es": "Jun"},
    {"en": "Jul", "es": "Jul"},
    {"en": "Aug", "es": "Ago"},
    {"en": "Sep", "es": "Sep"},
    {"en": "Oct", "es": "Oct"},
    {"en": "Nov", "es": "Nov"},
    {"en": "Dec", "es": "Dic"},
)


def _period_start(period: str, now: datetime, zone: ZoneInfo) -> datetime:
    local_now = now.astimezone(zone)
    if period == "today":
        start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        start = local_now - timedelta(days=7)
    elif period == "monthly":
        start = local_now - timedelta(days=30)
    elif period == "yearly":
        start = local_now - timedelta(days=365)
    else:
        start = local_now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    return start.astimezone(timezone.utc)


def _end(log: UserLog) -> datetime:
    return log.end_date or log.last_seen_at or log.start_date


def _overlap(
    log: UserLog, start: datetime, end: datetime
) -> tuple[datetime, datetime] | None:
    overlap_start = max(log.start_date, start)
    overlap_end = min(_end(log), end)
    if overlap_end < overlap_start:
        return None
    return overlap_start, overlap_end


def _metrics(logs: list[UserLog], start: datetime, end: datetime) -> dict[str, float]:
    sessions = [item for item in logs if _overlap(item, start, end) is not None]
    counts = Counter(item.user_id for item in sessions)
    durations = [
        max(0.0, (overlap[1] - overlap[0]).total_seconds() / 60)
        for item in sessions
        if (overlap := _overlap(item, start, end)) is not None
    ]
    return {
        "active": len(counts),
        "recurring": sum(count >= 2 for count in counts.values()),
        "average_minutes": (
            round(sum(durations) / len(durations), 2) if durations else 0
        ),
    }


def _trend(current: float, previous: float) -> str:
    return "up" if current >= previous else "down"


def _hour_label(hour: int) -> dict[str, str]:
    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12 or 12
    label = f"{display} {suffix}"
    return {"en": label, "es": label}


def _heatmap(
    logs: list[UserLog], start: datetime, end: datetime, zone: ZoneInfo
) -> list[dict]:
    active: dict[tuple[int, int], set[int]] = defaultdict(set)
    for log in logs:
        overlap = _overlap(log, start, end)
        if overlap is None:
            continue
        cursor = overlap[0].astimezone(zone).replace(minute=0, second=0, microsecond=0)
        local_end = overlap[1].astimezone(zone)
        first_bucket = cursor
        while cursor < local_end:
            active[(cursor.weekday(), cursor.hour)].add(log.user_id)
            cursor += timedelta(hours=1)
        if overlap[0] == overlap[1]:
            active[(first_bucket.weekday(), first_bucket.hour)].add(log.user_id)
    return [
        {
            "name": DAY_NAMES[weekday],
            "data": [
                {"x": _hour_label(hour), "y": len(active[(weekday, hour)])}
                for hour in range(24)
            ],
        }
        for weekday in range(7)
    ]


def _next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1)
    return value.replace(month=value.month + 1)


def _month_floor(value: datetime, zone: ZoneInfo) -> datetime:
    local = value.astimezone(zone)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _monthly_active(
    logs: list[UserLog], start: datetime, end: datetime, zone: ZoneInfo
) -> tuple[list[int], dict[str, list[str]]]:
    cursor = _month_floor(start, zone)
    last = _month_floor(end, zone)
    months: list[datetime] = []
    while cursor <= last:
        months.append(cursor)
        cursor = _next_month(cursor)

    values: list[int] = []
    for month in months:
        month_end = _next_month(month)
        users = {
            log.user_id
            for log in logs
            if _overlap(
                log,
                max(month.astimezone(timezone.utc), start),
                min(month_end.astimezone(timezone.utc), end),
            )
            is not None
        }
        values.append(len(users))

    categories = {
        lang: [
            (
                f"{MONTH_NAMES[month.month - 1][lang]} {month.year}"
                if len(months) > 12
                else MONTH_NAMES[month.month - 1][lang]
            )
            for month in months
        ]
        for lang in ("en", "es")
    }
    return values, categories


class UserActivityGraphicsService:
    @staticmethod
    async def get(
        period: str,
        company_id: int | None,
        *,
        now: datetime | None = None,
    ) -> dict:
        if period not in PERIODS:
            raise ValueError(f"Unsupported user activity period: {period}")
        current_end = now or datetime.now(timezone.utc)
        if current_end.tzinfo is None:
            current_end = current_end.replace(tzinfo=timezone.utc)
        zone = ZoneInfo(settings.DEFAULT_TIMEZONE)
        current_start = _period_start(period, current_end, zone)
        previous_start = current_start - (current_end - current_start)
        logs = await UserLogRepository.get_human_activity_between(
            previous_start, current_end, company_id
        )

        current = _metrics(logs, current_start, current_end)
        previous = _metrics(logs, previous_start, current_start)
        stale_cutoff = current_end - timedelta(
            seconds=settings.USER_LOG_STALE_TIMEOUT_SECONDS
        )
        online_users = {
            log.user_id
            for log in logs
            if (
                log.status == UserLogStatus.ONLINE
                or log.status == UserLogStatus.ONLINE.value
            )
            and log.end_date is None
            and log.last_seen_at is not None
            and log.last_seen_at >= stale_cutoff
        }
        previous_online = {
            log.user_id for log in logs if log.start_date <= current_start <= _end(log)
        }
        monthly_values, monthly_categories = _monthly_active(
            logs, current_start, current_end, zone
        )

        return {
            "period": period,
            "kpis": [
                {
                    "id": "kpiUsersOnline",
                    "name": {"en": "Online Users", "es": "Usuarios en línea"},
                    "value": len(online_users),
                    "unit": {"en": "Users", "es": "Usuarios"},
                    "trend": _trend(len(online_users), len(previous_online)),
                },
                {
                    "id": "kpiUsersAverageSessionTime",
                    "name": {
                        "en": "Average Session Time",
                        "es": "Tiempo promedio de sesión",
                    },
                    "value": current["average_minutes"],
                    "unit": {"en": "Minutes", "es": "Minutos"},
                    "trend": _trend(
                        current["average_minutes"], previous["average_minutes"]
                    ),
                },
                {
                    "id": "kpiUsersActiveUsers",
                    "name": {"en": "Active Users", "es": "Usuarios activos"},
                    "value": current["active"],
                    "unit": {"en": "Users", "es": "Usuarios"},
                    "trend": _trend(current["active"], previous["active"]),
                },
                {
                    "id": "kpiRecurringUsers",
                    "name": {
                        "en": "Recurring Users",
                        "es": "Usuarios recurrentes",
                    },
                    "value": current["recurring"],
                    "unit": {"en": "Users", "es": "Usuarios"},
                    "trend": _trend(current["recurring"], previous["recurring"]),
                },
            ],
            "graphics": [
                {
                    "id": "graphicUsersPerHour",
                    "type": "heatmap",
                    "title": {
                        "en": "Users per Hour",
                        "es": "Usuarios por Hora",
                    },
                    "data": _heatmap(logs, current_start, current_end, zone),
                },
                {
                    "id": "graphicUsersMAU",
                    "type": "bar",
                    "mode": "vertical",
                    "title": {
                        "en": "Monthly Active Users",
                        "es": "Usuarios activos mensuales",
                    },
                    "data": monthly_values,
                    "categories": monthly_categories,
                },
            ],
        }
