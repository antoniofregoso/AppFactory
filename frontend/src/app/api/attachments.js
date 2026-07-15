import { ClientError, gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const ATTACHMENTS_QUERY = gql`
  query SystemAttachments($modelUuid: UUID!, $recordUuid: UUID!) {
    systemAttachments(modelUuid: $modelUuid, recordUuid: $recordUuid) {
      uuid modelUuid recordUuid originalName contentType sizeBytes checksumSha256
      createdAt authorUuid authorName contentUrl
    }
  }
`;

const ATTACHMENT_CONTENT_QUERY = gql`
  query SystemAttachmentContent($attachmentUuid: UUID!) {
    systemAttachmentContent(attachmentUuid: $attachmentUuid) {
      contentBase64 contentType originalName
    }
  }
`;

const UPLOAD_ATTACHMENT_MUTATION = gql`
  mutation UploadSystemAttachment($attachment: SystemAttachmentUploadInput!) {
    uploadSystemAttachment(attachment: $attachment) {
      uuid modelUuid recordUuid originalName contentType sizeBytes checksumSha256
      createdAt authorUuid authorName contentUrl
    }
  }
`;

const DELETE_ATTACHMENT_MUTATION = gql`
  mutation DeleteSystemAttachment($attachmentUuid: UUID!) {
    deleteSystemAttachment(attachmentUuid: $attachmentUuid)
  }
`;

export class AttachmentUploadError extends Error {
    constructor(message, options) {
        super(message, options);
        this.name = 'AttachmentUploadError';
    }
}

function normalizeAttachment(item) {
    return {
        uuid: item.uuid,
        model_uuid: item.modelUuid,
        record_uuid: item.recordUuid,
        original_name: item.originalName,
        content_type: item.contentType,
        size_bytes: item.sizeBytes,
        checksum_sha256: item.checksumSha256,
        created_at: item.createdAt,
        author_uuid: item.authorUuid,
        author_name: item.authorName,
        content_url: item.contentUrl,
    };
}

function fileBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(',', 2)[1] ?? '');
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

function attachmentUuid(reference) {
    const value = String(reference ?? '');
    if (value.startsWith('attachment:')) return value.slice('attachment:'.length);
    return value.match(/\/attachments\/([^/]+)(?:\/content)?$/)?.[1] ?? value;
}

function base64Blob(contentBase64, contentType) {
    const binary = atob(contentBase64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    return new Blob([bytes], { type: contentType });
}

export async function uploadAttachment({ modelUuid, recordUuid, file }, fetchImpl = globalThis.fetch) {
    try {
        const data = await requestAuthenticated(UPLOAD_ATTACHMENT_MUTATION, {
            attachment: {
                modelUuid,
                recordUuid,
                originalName: file.name,
                contentType: file.type || 'application/octet-stream',
                contentBase64: await fileBase64(file),
            },
        }, fetchImpl);
        return normalizeAttachment(data.uploadSystemAttachment);
    } catch (error) {
        const message = error instanceof ClientError
            ? error.response.errors?.[0]?.message
            : error?.message;
        throw new AttachmentUploadError(message || 'Unable to upload attachment', { cause: error });
    }
}

export async function listAttachments({ modelUuid, recordUuid }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        ATTACHMENTS_QUERY, { modelUuid, recordUuid }, fetchImpl,
    );
    return data.systemAttachments.map(normalizeAttachment);
}

export async function fetchAttachmentContent(reference, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        ATTACHMENT_CONTENT_QUERY,
        { attachmentUuid: attachmentUuid(reference) },
        fetchImpl,
    );
    const content = data.systemAttachmentContent;
    return base64Blob(content.contentBase64, content.contentType);
}

export async function deleteAttachment(attachmentUuidValue, fetchImpl = globalThis.fetch) {
    await requestAuthenticated(
        DELETE_ATTACHMENT_MUTATION,
        { attachmentUuid: attachmentUuidValue },
        fetchImpl,
    );
}
