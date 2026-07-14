import uuid as uuid_lib
from time import monotonic

import strawberry

from app.core.config.settings import settings
from app.core.exceptions import AuthorizationException
from app.core.logging import get_logger
from app.core.security.jwt_bearer import IsAuthenticated
from app.core.security.jwt_manager import JWTManager
from app.domains.system.graphql.mappers import (
    system_message_to_type,
    system_model_to_type,
    system_notification_to_type,
    system_task_to_type,
    system_whatsapp_message_to_type,
    system_whatsapp_template_to_type,
    system_whatsapp_to_type,
)
from app.domains.system.graphql.types import (
    SystemMessageType,
    SystemModelSchemaUseType,
    SystemModelType,
    SystemModelViewType,
    SystemNotificationType,
    SystemPendingCountsType,
    SystemSearchErrorCode,
    SystemSearchErrorType,
    SystemSearchInput,
    SystemSearchResponseType,
    SystemSearchResultType,
    SystemSearchStatus,
    SystemTaskType,
    SystemWhatsAppMessageType,
    SystemWhatsAppTemplateType,
    SystemWhatsAppType,
)
from app.domains.system.search.compiler import SearchQueryCompilationError
from app.domains.system.search.temporal import SearchTimezoneError
from app.domains.system.search.validator import SearchPlanValidationError
from app.domains.system.service.system_message_service import SystemMessageService
from app.domains.system.service.system_model_service import SystemModelService
from app.domains.system.service.system_notification_service import (
    SystemNotificationService,
)
from app.domains.system.service.system_search_audit_service import (
    SystemSearchAuditService,
)
from app.domains.system.service.system_search_service import SystemSearchService
from app.domains.system.service.system_task_service import SystemTaskService
from app.domains.system.service.system_whatsapp_message_service import (
    SystemWhatsAppMessageService,
)
from app.domains.system.service.system_whatsapp_service import SystemWhatsAppService
from app.domains.system.service.system_whatsapp_template_service import (
    SystemWhatsAppTemplateService,
)
from app.domains.users.service.user_service import UserService

logger = get_logger(__name__)


async def _record_search_audit(
    *,
    request_id: uuid_lib.UUID,
    user_id: int,
    query: str,
    response: SystemSearchResponseType,
    started_at: float,
    queried_models: list[str] | tuple[str, ...] = (),
) -> None:
    try:
        await SystemSearchAuditService.record(
            request_id=request_id,
            user_id=user_id,
            query=query,
            status=response.status.value,
            models=list(queried_models),
            duration_ms=round((monotonic() - started_at) * 1000),
            result_count=len(response.results),
            error_codes=[error.code.value for error in response.errors],
        )
    except Exception:
        # Auditing is best effort and must not change the search response.
        logger.exception(
            "Unable to persist search audit",
            extra={"request_id": str(request_id), "user_id": user_id},
        )


async def get_current_user(info: strawberry.types.Info):
    request = info.context["request"]
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = JWTManager.verify_token(token, expected_token_type="access")
    user = await UserService.get_by_email(payload["sub"])
    if not user.active:
        raise AuthorizationException("User account is disabled")
    return user


def _ensure_whatsapp_belongs_to_company(whatsapp, company_id: int | None):
    if whatsapp.company_id != company_id:
        raise AuthorizationException(
            "WhatsApp configuration does not belong to your company"
        )


@strawberry.type
class SystemQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_models(self) -> list[SystemModelType]:
        models = await SystemModelService.get_all()
        return [system_model_to_type(model) for model in models]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_model(self, model_uuid: uuid_lib.UUID) -> SystemModelType:
        model = await SystemModelService.get_by_uuid(model_uuid)
        return system_model_to_type(model)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_model_by_name(self, name: str) -> SystemModelType:
        model = await SystemModelService.get_by_name(name)
        return system_model_to_type(model)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_model_view(
        self,
        model: str,
        use: SystemModelSchemaUseType,
        name: str,
        info: strawberry.types.Info,
        period: str | None = None,
    ) -> SystemModelViewType:
        user = await get_current_user(info)
        view = await SystemModelService.get_view(
            model,
            use,
            name,
            current_user_id=user.id,
            current_user=user,
            period=period,
        )
        return SystemModelViewType(model=view["model"], records=view["records"])

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_search(
        self, input: SystemSearchInput, info: strawberry.types.Info
    ) -> SystemSearchResponseType:
        user = await get_current_user(info)
        request_id = uuid_lib.uuid4()
        started_at = monotonic()
        try:
            execution = await SystemSearchService.run(
                input.query,
                current_user_id=user.id,
                lang=input.lang,
                limit=input.limit,
                mode=input.mode.value,
                model=input.model,
                original_query=input.original_query,
                clarification_answer=input.clarification_answer,
                timezone_name=settings.DEFAULT_TIMEZONE,
            )
            response = SystemSearchResponseType(
                request_id=request_id,
                status=SystemSearchStatus(execution.status),
                interpreted_query=execution.interpreted_query,
                needs_clarification=execution.needs_clarification,
                clarification_question=execution.clarification_question,
                results=[
                    SystemSearchResultType(**result.__dict__)
                    for result in execution.results
                ],
                errors=[
                    SystemSearchErrorType(
                        code=SystemSearchErrorCode(issue.code),
                        message=issue.message,
                        model=issue.model,
                        field=issue.field,
                    )
                    for issue in execution.errors
                ],
            )
            await _record_search_audit(
                request_id=request_id,
                user_id=user.id,
                query=input.query,
                response=response,
                started_at=started_at,
                queried_models=getattr(
                    execution.results,
                    "queried_models",
                    tuple(result.model for result in execution.results),
                ),
            )
            return response
        except (
            SearchPlanValidationError,
            SearchQueryCompilationError,
            SearchTimezoneError,
        ):
            logger.warning(
                "Rejected invalid search plan",
                extra={"request_id": str(request_id), "user_id": user.id},
            )
            message = (
                "El plan de búsqueda no es válido."
                if input.lang.startswith("es")
                else "The search plan is invalid."
            )
            response = SystemSearchResponseType(
                request_id=request_id,
                status=SystemSearchStatus.FAILED,
                interpreted_query=input.query,
                needs_clarification=False,
                clarification_question=None,
                results=[],
                errors=[
                    SystemSearchErrorType(
                        code=SystemSearchErrorCode.INVALID_PLAN,
                        message=message,
                    )
                ],
            )
            await _record_search_audit(
                request_id=request_id,
                user_id=user.id,
                query=input.query,
                response=response,
                started_at=started_at,
            )
            return response
        except TimeoutError:
            logger.warning(
                "Search timed out",
                extra={"request_id": str(request_id), "user_id": user.id},
            )
            message = (
                "La búsqueda agotó el tiempo disponible."
                if input.lang.startswith("es")
                else "The search timed out."
            )
            response = SystemSearchResponseType(
                request_id=request_id,
                status=SystemSearchStatus.FAILED,
                interpreted_query=input.query,
                needs_clarification=False,
                clarification_question=None,
                results=[],
                errors=[
                    SystemSearchErrorType(
                        code=SystemSearchErrorCode.TIMEOUT,
                        message=message,
                    )
                ],
            )
            await _record_search_audit(
                request_id=request_id,
                user_id=user.id,
                query=input.query,
                response=response,
                started_at=started_at,
            )
            return response
        except Exception:
            logger.exception(
                "Unexpected search failure",
                extra={"request_id": str(request_id), "user_id": user.id},
            )
            message = (
                "No se pudo completar la búsqueda."
                if input.lang.startswith("es")
                else "The search could not be completed."
            )
            response = SystemSearchResponseType(
                request_id=request_id,
                status=SystemSearchStatus.FAILED,
                interpreted_query=input.query,
                needs_clarification=False,
                clarification_question=None,
                results=[],
                errors=[
                    SystemSearchErrorType(
                        code=SystemSearchErrorCode.INTERNAL_ERROR,
                        message=message,
                    )
                ],
            )
            await _record_search_audit(
                request_id=request_id,
                user_id=user.id,
                query=input.query,
                response=response,
                started_at=started_at,
            )
            return response

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_messages(self) -> list[SystemMessageType]:
        messages = await SystemMessageService.get_all()
        return [system_message_to_type(message) for message in messages]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_message(self, message_uuid: uuid_lib.UUID) -> SystemMessageType:
        message = await SystemMessageService.get_by_uuid(message_uuid)
        return system_message_to_type(message)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_notifications(self) -> list[SystemNotificationType]:
        notifications = await SystemNotificationService.get_all()
        return [
            system_notification_to_type(notification) for notification in notifications
        ]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_notification(
        self, notification_uuid: uuid_lib.UUID
    ) -> SystemNotificationType:
        notification = await SystemNotificationService.get_by_uuid(notification_uuid)
        return system_notification_to_type(notification)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_my_notifications(
        self, info: strawberry.types.Info, limit: int = 30
    ) -> list[SystemNotificationType]:
        user = await get_current_user(info)
        notifications = await SystemNotificationService.get_recent_by_user_id(
            user.id, limit
        )
        return [
            system_notification_to_type(notification) for notification in notifications
        ]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_tasks(self) -> list[SystemTaskType]:
        tasks = await SystemTaskService.get_all()
        return [system_task_to_type(task) for task in tasks]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_task(self, task_uuid: uuid_lib.UUID) -> SystemTaskType:
        task = await SystemTaskService.get_by_uuid(task_uuid)
        return system_task_to_type(task)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_pending_counts(
        self, info: strawberry.types.Info
    ) -> SystemPendingCountsType:
        user = await get_current_user(info)
        messages = await SystemMessageService.count_unread_by_user_id(user.id)
        notifications = await SystemNotificationService.count_unread_by_user_id(user.id)
        return SystemPendingCountsType(
            messages=messages,
            notifications=notifications,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_push_public_key(self) -> str:
        return settings.VAPID_PUBLIC_KEY

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp_configurations(
        self, info: strawberry.types.Info
    ) -> list[SystemWhatsAppType]:
        user = await get_current_user(info)
        configurations = await SystemWhatsAppService.get_all(user.company_id)
        return [system_whatsapp_to_type(whatsapp) for whatsapp in configurations]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp(
        self, whatsapp_uuid: uuid_lib.UUID, info: strawberry.types.Info
    ) -> SystemWhatsAppType:
        user = await get_current_user(info)
        whatsapp = await SystemWhatsAppService.get_by_uuid(whatsapp_uuid)
        _ensure_whatsapp_belongs_to_company(whatsapp, user.company_id)
        return system_whatsapp_to_type(whatsapp)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp_templates(
        self, whatsapp_uuid: uuid_lib.UUID, info: strawberry.types.Info
    ) -> list[SystemWhatsAppTemplateType]:
        user = await get_current_user(info)
        whatsapp = await SystemWhatsAppService.get_by_uuid(whatsapp_uuid)
        _ensure_whatsapp_belongs_to_company(whatsapp, user.company_id)
        templates = await SystemWhatsAppTemplateService.get_all_by_whatsapp(
            whatsapp_uuid
        )
        return [system_whatsapp_template_to_type(template) for template in templates]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp_template(
        self, template_uuid: uuid_lib.UUID
    ) -> SystemWhatsAppTemplateType:
        template = await SystemWhatsAppTemplateService.get_by_uuid(template_uuid)
        return system_whatsapp_template_to_type(template)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp_messages(
        self, whatsapp_uuid: uuid_lib.UUID, info: strawberry.types.Info
    ) -> list[SystemWhatsAppMessageType]:
        user = await get_current_user(info)
        whatsapp = await SystemWhatsAppService.get_by_uuid(whatsapp_uuid)
        _ensure_whatsapp_belongs_to_company(whatsapp, user.company_id)
        messages = await SystemWhatsAppMessageService.get_all_by_whatsapp(whatsapp_uuid)
        return [system_whatsapp_message_to_type(message) for message in messages]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system_whatsapp_message(
        self, message_uuid: uuid_lib.UUID
    ) -> SystemWhatsAppMessageType:
        message = await SystemWhatsAppMessageService.get_by_uuid(message_uuid)
        return system_whatsapp_message_to_type(message)
