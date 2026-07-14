import { requestAuthenticatedFetch } from './session.js';

export class AttachmentUploadError extends Error {
    constructor(message, options) {
        super(message, options);
        this.name = 'AttachmentUploadError';
    }
}

async function uploadErrorMessage(response) {
    const fallback = `Unable to upload attachment (${response.status})`;
    try {
        const data = await response.json();
        return data?.message || data?.detail || fallback;
    } catch {
        return fallback;
    }
}

export async function uploadAttachment(
    { modelUuid, recordUuid, file },
    fetchImpl = globalThis.fetch,
) {
    const form = new FormData();
    form.set('model_uuid', modelUuid);
    form.set('record_uuid', recordUuid);
    form.set('file', file);

    const response = await requestAuthenticatedFetch(
        '/api/system/attachments',
        { method: 'POST', body: form },
        fetchImpl,
    );
    if (!response.ok) {
        throw new AttachmentUploadError(await uploadErrorMessage(response));
    }
    return response.json();
}

export async function listAttachments(
    { modelUuid, recordUuid },
    fetchImpl = globalThis.fetch,
) {
    const response = await requestAuthenticatedFetch(
        `/api/system/attachments/record/${encodeURIComponent(modelUuid)}/${encodeURIComponent(recordUuid)}`,
        {},
        fetchImpl,
    );
    if (!response.ok) {
        throw new Error(`Unable to load attachments (${response.status})`);
    }
    return response.json();
}

export async function fetchAttachmentContent(contentUrl, fetchImpl = globalThis.fetch) {
    const response = await requestAuthenticatedFetch(contentUrl, {}, fetchImpl);
    if (!response.ok) {
        throw new Error(`Unable to open attachment (${response.status})`);
    }
    return response.blob();
}

export async function deleteAttachment(attachmentUuid, fetchImpl = globalThis.fetch) {
    const response = await requestAuthenticatedFetch(
        `/api/system/attachments/${encodeURIComponent(attachmentUuid)}`,
        { method: 'DELETE' },
        fetchImpl,
    );
    if (!response.ok) {
        throw new Error(`Unable to delete attachment (${response.status})`);
    }
}
