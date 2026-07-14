"""Servidor MCP de solo lectura para generar reportes a directores.

Se conecta vía HTTP (Streamable HTTP transport) y se monta dentro de la app
FastAPI principal en `/mcp` (ver main.py). La autenticación es manual con un
token MCP de larga duración (ver app/mcp/auth.py) en vez de usar el
`token_verifier`/`auth` de FastMCP, para no activar el flujo de descubrimiento
OAuth: aquí reutilizamos el JWT existente de la aplicación.
"""

from mcp.server.fastmcp import Context, FastMCP

from app.core.config.settings import settings
from app.mcp.auth import get_authenticated_user
from app.mcp import reports

mcp = FastMCP(
    name=settings.APP_NAME,
    instructions=(
        "Reportes de solo lectura sobre tareas, actividad de equipo y "
        "usuarios de la compañía del usuario autenticado. Requiere un token "
        "MCP (generado con la mutación GraphQL generateMcpToken) enviado "
        "como 'Authorization: Bearer <token>'."
    ),
    stateless_http=True,
)


@mcp.tool()
async def get_tasks_report(ctx: Context) -> dict:
    """Resumen de tareas de la compañía del usuario: totales por estado y
    prioridad, cantidad de tareas vencidas y el detalle de hasta 10 de ellas."""
    user = await get_authenticated_user(ctx)
    return await reports.tasks_report(user.company_id)


@mcp.tool()
async def get_team_activity_report(ctx: Context, days: int = 7) -> dict:
    """Actividad reciente del equipo de la compañía del usuario: usuarios
    activos, sesiones y minutos conectados en los últimos `days` días
    (7 por defecto)."""
    user = await get_authenticated_user(ctx)
    return await reports.team_activity_report(user.company_id, days=days)


@mcp.tool()
async def get_users_overview(ctx: Context) -> dict:
    """Listado de usuarios de la compañía del usuario autenticado, con su
    estado (activo/inactivo) y último acceso registrado."""
    user = await get_authenticated_user(ctx)
    return await reports.users_overview(user.company_id)


mcp_app = mcp.streamable_http_app()
