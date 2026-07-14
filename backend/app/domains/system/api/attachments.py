import uuid as uuid_lib

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.domains.system.api.dependencies import get_current_user
from app.domains.system.api.schemas import SystemAttachmentResponse
from app.domains.system.service.system_attachment_service import (
    SystemAttachmentService,
)
from app.domains.users.models.user_user import UserUser

router = APIRouter(prefix="/api/system/attachments", tags=["system-attachments"])


@router.post("", response_model=SystemAttachmentResponse, status_code=201)
async def upload_attachment(
    model_uuid: uuid_lib.UUID = Form(...),
    record_uuid: uuid_lib.UUID = Form(...),
    file: UploadFile = File(...),
    user: UserUser = Depends(get_current_user),
) -> SystemAttachmentResponse:
    attachment = await SystemAttachmentService.create(
        model_uuid=model_uuid,
        record_uuid=record_uuid,
        original_name=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        stream=file.file,
        user_id=user.id,
        company_id=user.company_id,
    )
    return SystemAttachmentResponse.from_attachment(
        attachment,
        model_uuid,
        author_uuid=user.uuid,
        author_name=user.name,
    )


@router.get(
    "/record/{model_uuid}/{record_uuid}",
    response_model=list[SystemAttachmentResponse],
)
async def list_attachments(
    model_uuid: uuid_lib.UUID,
    record_uuid: uuid_lib.UUID,
    user: UserUser = Depends(get_current_user),
) -> list[SystemAttachmentResponse]:
    rows = await SystemAttachmentService.get_all_for_record(
        model_uuid,
        record_uuid,
        user.company_id,
    )
    return [
        SystemAttachmentResponse.from_attachment(
            attachment,
            model_uuid,
            author_uuid=author_uuid,
            author_name=author_name,
        )
        for attachment, author_uuid, author_name in rows
    ]


@router.get("/{attachment_uuid}/content", response_class=FileResponse)
async def download_attachment(
    attachment_uuid: uuid_lib.UUID,
    user: UserUser = Depends(get_current_user),
) -> FileResponse:
    attachment, path = await SystemAttachmentService.get_content(
        attachment_uuid,
        user.company_id,
    )
    return FileResponse(
        path=path,
        media_type=attachment.content_type,
        filename=attachment.original_name,
        content_disposition_type=(
            "inline" if attachment.content_type.startswith("image/") else "attachment"
        ),
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete("/{attachment_uuid}", status_code=204)
async def delete_attachment(
    attachment_uuid: uuid_lib.UUID,
    user: UserUser = Depends(get_current_user),
) -> None:
    await SystemAttachmentService.delete(attachment_uuid, user.company_id)
