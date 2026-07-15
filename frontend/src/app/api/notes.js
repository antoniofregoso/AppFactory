import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const NOTES_QUERY = gql`
  query SystemNotes($modelUuid: UUID!, $recordUuid: UUID!) {
    systemNotes(modelUuid: $modelUuid, recordUuid: $recordUuid) {
      uuid modelUuid recordUuid contentHtml authorUuid authorName createdAt
    }
  }
`;

const CREATE_NOTE_MUTATION = gql`
  mutation CreateSystemNote($note: SystemNoteCreateInput!) {
    createSystemNote(note: $note) {
      uuid modelUuid recordUuid contentHtml authorUuid authorName createdAt
    }
  }
`;

const DELETE_NOTE_MUTATION = gql`
  mutation DeleteSystemNote($noteUuid: UUID!) {
    deleteSystemNote(noteUuid: $noteUuid)
  }
`;

function normalizeNote(item) {
    return {
        uuid: item.uuid,
        model_uuid: item.modelUuid,
        record_uuid: item.recordUuid,
        content_html: item.contentHtml,
        author_uuid: item.authorUuid,
        author_name: item.authorName,
        created_at: item.createdAt,
    };
}

export async function listNotes({ modelUuid, recordUuid }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(NOTES_QUERY, { modelUuid, recordUuid }, fetchImpl);
    return data.systemNotes.map(normalizeNote);
}

export async function createNote({ modelUuid, recordUuid, contentHtml }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(CREATE_NOTE_MUTATION, {
        note: { modelUuid, recordUuid, contentHtml },
    }, fetchImpl);
    return normalizeNote(data.createSystemNote);
}

export async function deleteNote(noteUuid, fetchImpl = globalThis.fetch) {
    await requestAuthenticated(DELETE_NOTE_MUTATION, { noteUuid }, fetchImpl);
}
