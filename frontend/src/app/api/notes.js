import { requestAuthenticatedFetch } from './session.js';

async function parseError(response, fallback) {
    try {
        const data = await response.json();
        return data?.message || data?.detail || fallback;
    } catch {
        return fallback;
    }
}

export async function listNotes({ modelUuid, recordUuid }, fetchImpl = globalThis.fetch) {
    const response = await requestAuthenticatedFetch(
        `/api/system/notes/record/${encodeURIComponent(modelUuid)}/${encodeURIComponent(recordUuid)}`,
        {},
        fetchImpl,
    );
    if (!response.ok) throw new Error(await parseError(response, `Unable to load notes (${response.status})`));
    return response.json();
}

export async function createNote({ modelUuid, recordUuid, contentHtml }, fetchImpl = globalThis.fetch) {
    const response = await requestAuthenticatedFetch('/api/system/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_uuid: modelUuid, record_uuid: recordUuid, content_html: contentHtml }),
    }, fetchImpl);
    if (!response.ok) throw new Error(await parseError(response, `Unable to create note (${response.status})`));
    return response.json();
}

export async function deleteNote(noteUuid, fetchImpl = globalThis.fetch) {
    const response = await requestAuthenticatedFetch(
        `/api/system/notes/${encodeURIComponent(noteUuid)}`,
        { method: 'DELETE' },
        fetchImpl,
    );
    if (!response.ok) throw new Error(await parseError(response, `Unable to delete note (${response.status})`));
}
