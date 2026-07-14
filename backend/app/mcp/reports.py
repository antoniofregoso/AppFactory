"""Agregaciones de solo lectura usadas por las tools MCP.

Estas funciones reciben `company_id` (nunca `ctx`/HTTP) para poder probarse
con pytest sin levantar el transporte MCP.
"""

from datetime import datetime, timedelta, timezone

from app.domains.system.models.system_task import TaskStatus
from app.domains.system.service.system_task_service import SystemTaskService
from app.domains.users.service.user_log_service import UserLogService
from app.domains.users.service.user_service import UserService


async def _company_user_ids(company_id: int | None) -> set[int]:
    users = await UserService.get_all()
    return {user.id for user in users if user.company_id == company_id}


async def tasks_report(company_id: int | None) -> dict:
    """Resumen de tareas de la compañía: totales por estado/prioridad y vencidas."""
    user_ids = await _company_user_ids(company_id)
    all_tasks = await SystemTaskService.get_all()
    tasks = [
        task
        for task in all_tasks
        if task.user_id in user_ids
        or (task.user_id is None and task.create_by in user_ids)
    ]

    now = datetime.now(timezone.utc)
    by_status = {status.value: 0 for status in TaskStatus}
    by_priority: dict[str, int] = {}
    overdue = []

    for task in tasks:
        by_status[task.status] = by_status.get(task.status, 0) + 1
        by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
        if (
            task.date_due is not None
            and task.date_due < now
            and task.status != TaskStatus.completed
        ):
            overdue.append(task)

    overdue.sort(key=lambda task: task.date_due)

    return {
        "total": len(tasks),
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue_count": len(overdue),
        "overdue_tasks": [
            {
                "title": task.get_title(),
                "status": task.status,
                "priority": task.priority,
                "due_date": task.date_due.isoformat(),
                "assigned_to": task.user.name if task.user else None,
            }
            for task in overdue[:10]
        ],
    }


async def team_activity_report(company_id: int | None, days: int = 7) -> dict:
    """Actividad reciente del equipo de la compañía a partir de los logs de sesión."""
    users = await UserService.get_all()
    company_users = [user for user in users if user.company_id == company_id]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    active_users = []
    total_duration_ms = 0
    for user in company_users:
        logs = await UserLogService.get_by_user_id(user.id, limit=200)
        recent_logs = [log for log in logs if log.start_date >= cutoff]
        if not recent_logs:
            continue

        duration_ms = sum(log.duration or 0 for log in recent_logs)
        total_duration_ms += duration_ms
        last_seen = max(log.last_seen_at or log.start_date for log in recent_logs)

        active_users.append(
            {
                "name": user.name,
                "email": user.email,
                "sessions": len(recent_logs),
                "duration_minutes": round(duration_ms / 1000 / 60, 1),
                "last_seen_at": last_seen.isoformat(),
            }
        )

    active_users.sort(key=lambda item: item["duration_minutes"], reverse=True)

    return {
        "period_days": days,
        "total_company_users": len(company_users),
        "active_user_count": len(active_users),
        "total_duration_minutes": round(total_duration_ms / 1000 / 60, 1),
        "users": active_users,
    }


async def users_overview(company_id: int | None) -> dict:
    """Listado de usuarios de la compañía con su estado y último acceso."""
    users = await UserService.get_all()
    company_users = [user for user in users if user.company_id == company_id]

    overview = []
    for user in company_users:
        logs = await UserLogService.get_by_user_id(user.id, limit=1)
        last_log = logs[0] if logs else None
        overview.append(
            {
                "name": user.name,
                "email": user.email,
                "active": user.active,
                "user_type": user.user_type,
                "last_seen_at": (
                    (last_log.last_seen_at or last_log.start_date).isoformat()
                    if last_log
                    else None
                ),
            }
        )

    return {
        "total_users": len(company_users),
        "active_users": sum(1 for user in company_users if user.active),
        "inactive_users": sum(1 for user in company_users if not user.active),
        "users": overview,
    }
