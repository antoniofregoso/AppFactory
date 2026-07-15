import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({ requestAuthenticated: vi.fn() }));

import { deleteAttachment, fetchAttachmentContent, listAttachments, uploadAttachment } from '../src/app/api/attachments.js';
import { requestAuthenticated } from '../src/app/api/session.js';

afterEach(() => requestAuthenticated.mockReset());

describe('attachments GraphQL API', () => {
    it('lists and normalizes attachment metadata', async () => {
        requestAuthenticated.mockResolvedValue({ systemAttachments: [{
            uuid: 'attachment-1', modelUuid: 'model-1', recordUuid: 'record-1',
            originalName: 'contract.pdf', contentType: 'application/pdf', sizeBytes: 12,
            checksumSha256: 'abc', createdAt: 'now', authorUuid: 'user-1',
            authorName: 'Ana', contentUrl: 'attachment:attachment-1',
        }] });
        const [item] = await listAttachments({ modelUuid: 'model-1', recordUuid: 'record-1' });
        expect(item).toMatchObject({ original_name: 'contract.pdf', content_url: 'attachment:attachment-1' });
        expect(requestAuthenticated.mock.calls[0][1]).toEqual({ modelUuid: 'model-1', recordUuid: 'record-1' });
    });

    it('uploads files as base64 and normalizes the response', async () => {
        requestAuthenticated.mockResolvedValue({ uploadSystemAttachment: {
            uuid: 'attachment-1', modelUuid: 'model-1', recordUuid: 'record-1',
            originalName: 'ok.png', contentType: 'image/png', sizeBytes: 2,
            checksumSha256: 'abc', createdAt: 'now', authorUuid: null,
            authorName: null, contentUrl: 'attachment:attachment-1',
        } });
        const result = await uploadAttachment({
            modelUuid: 'model-1', recordUuid: 'record-1',
            file: new File(['ok'], 'ok.png', { type: 'image/png' }),
        });
        expect(result.content_url).toBe('attachment:attachment-1');
        expect(requestAuthenticated.mock.calls[0][1].attachment).toMatchObject({
            modelUuid: 'model-1', recordUuid: 'record-1', originalName: 'ok.png', contentType: 'image/png',
        });
        expect(requestAuthenticated.mock.calls[0][1].attachment.contentBase64).toBe('b2s=');
    });

    it('downloads attachment content through GraphQL', async () => {
        requestAuthenticated.mockResolvedValue({ systemAttachmentContent: {
            contentBase64: 'ZG9jdW1lbnQ=', contentType: 'application/pdf', originalName: 'file.pdf',
        } });
        const blob = await fetchAttachmentContent('attachment:attachment-1');
        expect(blob.type).toBe('application/pdf');
        expect(blob.size).toBe(8);
        expect(requestAuthenticated.mock.calls[0][1]).toEqual({ attachmentUuid: 'attachment-1' });
    });

    it('deletes an attachment through GraphQL', async () => {
        requestAuthenticated.mockResolvedValue({ deleteSystemAttachment: true });
        await deleteAttachment('attachment-1');
        expect(requestAuthenticated.mock.calls[0][1]).toEqual({ attachmentUuid: 'attachment-1' });
    });
});
