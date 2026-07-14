import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({
    requestAuthenticatedFetch: vi.fn(),
}));

import { deleteAttachment, fetchAttachmentContent, listAttachments, uploadAttachment } from '../src/app/api/attachments.js';
import { requestAuthenticatedFetch } from '../src/app/api/session.js';

afterEach(() => {
    requestAuthenticatedFetch.mockReset();
});

describe('attachments API', () => {
    it('deletes an attachment with authentication', async () => {
        requestAuthenticatedFetch.mockResolvedValue({ ok: true });

        await expect(deleteAttachment('attachment-1')).resolves.toBeUndefined();
        expect(requestAuthenticatedFetch).toHaveBeenCalledWith(
            '/api/system/attachments/attachment-1', { method: 'DELETE' }, expect.any(Function),
        );
    });
    it('loads attachment content with authentication', async () => {
        const blob = new Blob(['document'], { type: 'application/pdf' });
        requestAuthenticatedFetch.mockResolvedValue({ ok: true, blob: vi.fn().mockResolvedValue(blob) });

        await expect(fetchAttachmentContent('/api/system/attachments/attachment-1/content')).resolves.toBe(blob);
        expect(requestAuthenticatedFetch).toHaveBeenCalledWith(
            '/api/system/attachments/attachment-1/content', {}, expect.any(Function),
        );
    });
    it('loads attachments stored for a record', async () => {
        const attachments = [{ uuid: 'attachment-1', original_name: 'contract.pdf', size_bytes: 12 }];
        requestAuthenticatedFetch.mockResolvedValue({ ok: true, json: vi.fn().mockResolvedValue(attachments) });

        await expect(listAttachments({ modelUuid: 'model-1', recordUuid: 'record-1' })).resolves.toEqual(attachments);
        expect(requestAuthenticatedFetch).toHaveBeenCalledWith(
            '/api/system/attachments/record/model-1/record-1', {}, expect.any(Function),
        );
    });
    it('includes backend validation messages in upload errors', async () => {
        requestAuthenticatedFetch.mockResolvedValue(new Response(JSON.stringify({
            message: 'Attachment content type is not allowed',
        }), {
            status: 422,
            headers: { 'Content-Type': 'application/json' },
        }));

        await expect(uploadAttachment({
            modelUuid: 'model-1',
            recordUuid: 'record-1',
            file: new File(['bad'], 'bad.svg', { type: 'image/svg+xml' }),
        })).rejects.toMatchObject({
            name: 'AttachmentUploadError',
            message: 'Attachment content type is not allowed',
        });
    });

    it('returns uploaded attachment metadata', async () => {
        requestAuthenticatedFetch.mockResolvedValue(new Response(JSON.stringify({
            content_url: '/api/system/attachments/attachment-1/content',
        }), {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
        }));

        await expect(uploadAttachment({
            modelUuid: 'model-1',
            recordUuid: 'record-1',
            file: new File(['ok'], 'ok.png', { type: 'image/png' }),
        })).resolves.toEqual({
            content_url: '/api/system/attachments/attachment-1/content',
        });
    });
});
