import uvicorn
import asyncio
from contextlib import AsyncExitStack
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import strawberry
from sqlalchemy.sql import text
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.database.session import db
from app.core.config.settings import settings
from app.core.exceptions import AppException

from app.domains.system.graphql.mutations import SystemMutation
from app.domains.system.graphql.queries import SystemQuery
from app.domains.system.api import attachment_router, note_router
from app.domains.users.graphql.queries import UserQuery
from app.domains.users.graphql.mutations import UserMutation
from app.domains.users.service.user_log_service import UserLogService
from app.domains.system.service.system_task_reminder_service import (
    SystemTaskReminderService,
)
from app.domains.system.search.registry import validate_configured_search_models
from app.mcp.server import mcp, mcp_app

from strawberry.fastapi import GraphQLRouter
from app.core.logging import configure_logging, get_logger

# Configurar logging al inicio
configure_logging()
logger = get_logger(__name__)

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)


@strawberry.type
class Query(UserQuery, SystemQuery):
    pass


@strawberry.type
class Mutation(UserMutation, SystemMutation):
    pass


def create_error_response(
    status_code: int, error_code: str, message: str, details=None
):
    """Crea una respuesta de error estructurada."""
    return {
        "status_code": status_code,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def init_app():
    async def close_stale_user_logs_periodically():
        while True:
            await asyncio.sleep(settings.USER_LOG_SWEEP_INTERVAL_SECONDS)
            try:
                closed_count = await UserLogService.close_stale_logs()
                if closed_count:
                    logger.info("Closed %s stale user activity logs", closed_count)
            except Exception as exc:
                logger.exception("Failed to close stale user activity logs: %s", exc)

    async def sweep_task_reminders_periodically():
        while True:
            await asyncio.sleep(settings.TASK_REMINDER_SWEEP_INTERVAL_SECONDS)
            try:
                created = await SystemTaskReminderService.sweep()
                if created:
                    logger.info("Generated %s task reminder notifications", created)
            except Exception as exc:
                logger.exception("Failed to sweep task reminders: %s", exc)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logger.info("Iniciando aplicación...")
        await validate_configured_search_models()
        stale_logs_task = asyncio.create_task(close_stale_user_logs_periodically())
        task_reminders_task = asyncio.create_task(sweep_task_reminders_periodically())
        async with AsyncExitStack() as stack:
            # El servidor MCP (montado en /mcp) trae su propio lifespan
            # (session manager de Streamable HTTP) que hay que iniciar aquí,
            # de lo contrario las tool calls fallan al no haber un task group activo.
            await stack.enter_async_context(mcp.session_manager.run())
            try:
                yield
            finally:
                stale_logs_task.cancel()
                task_reminders_task.cancel()
                with suppress(asyncio.CancelledError):
                    await stale_logs_task
                with suppress(asyncio.CancelledError):
                    await task_reminders_task
                logger.info("Cerrando conexión a base de datos...")
                await db.close()

    apps = FastAPI(
        title=settings.APP_NAME,
        description="API description",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    apps.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    # Exception Handlers
    @apps.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(
            f"AppException: {exc.error_code} - {exc.message}",
            extra={"status_code": exc.status_code, "details": exc.details},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                exc.status_code, exc.error_code, exc.message, exc.details
            ),
        )

    @apps.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.warning(f"Validation error on {request.url}: {exc.errors()}")
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"][1:]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        return JSONResponse(
            status_code=422,
            content=create_error_response(
                422, "VALIDATION_ERROR", "Request validation failed", {"errors": errors}
            ),
        )

    @apps.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                {} if not settings.LOG_LEVEL == "DEBUG" else {"error": str(exc)},
            ),
        )

    @apps.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
        return JSONResponse(
            status_code=429,
            content=create_error_response(
                429,
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Please try again later.",
            ),
        )

    # Aplicar rate limiter a la app
    apps.state.limiter = limiter
    apps.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    @apps.get("/")
    async def root():
        return {"message": "Hello World"}

    @apps.get("/health")
    async def health_check():
        try:
            async with db.session() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "online"}
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "offline", "error": str(e)},
            )

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    graphql_app = GraphQLRouter(schema)

    apps.include_router(graphql_app, prefix="/graphql")
    apps.include_router(attachment_router)
    apps.include_router(note_router)
    # Mounted at root (not "/mcp") because FastMCP's own streamable_http_path
    # already defaults to "/mcp" internally; mounting this at "/mcp" too would
    # nest it under "/mcp/mcp" and break the documented /mcp endpoint.
    apps.mount("/", mcp_app)

    return apps


app = init_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
