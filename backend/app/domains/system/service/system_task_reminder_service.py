from datetime import datetime, timedelta, timezone

from app.core.config.settings import settings
from app.domains.system.models.system_notification import NotificationPriority
from app.domains.system.service.system_notification_service import (
    SystemNotificationService,
)
from app.domains.system.service.system_task_service import SystemTaskService

# (date field on SystemTask, minutes before the event, priority, reminder key)
_REMINDER_RULES = [
    ("date_assign", "start_early", NotificationPriority.info),
    ("date_assign", "start_final", NotificationPriority.danger),
    ("date_due", "due_early", NotificationPriority.warning),
    ("date_due", "due_final", NotificationPriority.danger),
]

_TITLES = {
    "start_early": {
        "es": "Tarea por comenzar",
        "en": "Task starting soon",
    },
    "start_final": {
        "es": "La tarea comienza en 5 minutos",
        "en": "Task starts in 5 minutes",
    },
    "due_early": {
        "es": "Tarea por vencer",
        "en": "Task due soon",
    },
    "due_final": {
        "es": "La tarea vence en 5 minutos",
        "en": "Task is due in 5 minutes",
    },
}


def _offset_minutes(kind: str) -> int:
    return (
        settings.TASK_REMINDER_FINAL_MINUTES
        if kind.endswith("_final")
        else settings.TASK_REMINDER_EARLY_MINUTES
    )


def _build_message(kind: str, task) -> dict:
    task_title_es = task.get_title("es", "en")
    task_title_en = task.get_title("en", "es")
    return {
        "es": f"{_TITLES[kind]['es']}: {task_title_es}".strip(": "),
        "en": f"{_TITLES[kind]['en']}: {task_title_en}".strip(": "),
    }


class SystemTaskReminderService:
    """Generates SystemNotification reminders for task start/due dates."""

    @staticmethod
    async def sweep() -> int:
        now = datetime.now(timezone.utc)
        tasks = await SystemTaskService.get_pending_with_reminder_dates()

        due_reminders = []
        for task in tasks:
            for date_field, kind, priority in _REMINDER_RULES:
                event_time = getattr(task, date_field)
                if event_time is None:
                    continue
                trigger_time = event_time - timedelta(minutes=_offset_minutes(kind))
                if trigger_time <= now <= event_time:
                    due_reminders.append((task, kind, priority))

        if not due_reminders:
            return 0

        dedupe_keys = [
            f"task_reminder:{task.uuid}:{kind}" for task, kind, _ in due_reminders
        ]
        existing_keys = await SystemNotificationService.get_existing_dedupe_keys(
            dedupe_keys
        )

        created = 0
        for task, kind, priority in due_reminders:
            dedupe_key = f"task_reminder:{task.uuid}:{kind}"
            if dedupe_key in existing_keys:
                continue
            await SystemNotificationService.create(
                {
                    "title": dict(_TITLES[kind]),
                    "message": _build_message(kind, task),
                    "priority": priority,
                    "status": "sent",
                    "read": False,
                    "active": True,
                    "dedupe_key": dedupe_key,
                    "user_id": task.user_id,
                }
            )
            created += 1
        return created
