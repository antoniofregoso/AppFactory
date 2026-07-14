import uuid as uuid_lib

from fastapi import APIRouter, Depends

from app.domains.system.api.dependencies import get_current_user
from app.domains.system.api.schemas import SystemNoteCreate, SystemNoteResponse
from app.domains.system.service.system_note_service import SystemNoteService
from app.domains.users.models.user_user import UserUser

router = APIRouter(prefix="/api/system/notes", tags=["system-notes"])


def note_response(note, model_uuid, author=None):
    return SystemNoteResponse(
        uuid=note.uuid,
        model_uuid=model_uuid,
        record_uuid=note.record_uuid,
        content_html=note.content_html,
        author_uuid=author[0] if author else None,
        author_name=author[1] if author else None,
        created_at=note.created_at,
    )


@router.post("", response_model=SystemNoteResponse, status_code=201)
async def create_note(payload: SystemNoteCreate, user: UserUser = Depends(get_current_user)):
    note, author = await SystemNoteService.create(
        model_uuid=payload.model_uuid,
        record_uuid=payload.record_uuid,
        content_html=payload.content_html,
        user_id=user.id,
        company_id=user.company_id,
    )
    return note_response(note, payload.model_uuid, author)


@router.get("/record/{model_uuid}/{record_uuid}", response_model=list[SystemNoteResponse])
async def list_notes(model_uuid: uuid_lib.UUID, record_uuid: uuid_lib.UUID, user: UserUser = Depends(get_current_user)):
    rows = await SystemNoteService.get_all_for_record(model_uuid, record_uuid, user.company_id)
    return [
        note_response(note, model_uuid, (author_uuid, author_name))
        for note, author_uuid, author_name in rows
    ]


@router.delete("/{note_uuid}", status_code=204)
async def delete_note(note_uuid: uuid_lib.UUID, user: UserUser = Depends(get_current_user)):
    await SystemNoteService.delete(note_uuid, user.company_id)
