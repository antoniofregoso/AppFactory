import { afterEach, describe, expect, it, vi } from 'vitest';
import { render } from 'preact';

vi.mock('../src/app/api/attachments.js', () => ({
    uploadAttachment: vi.fn().mockResolvedValue({
        content_url: '/api/system/attachments/attachment-1/content',
    }),
}));
vi.mock('../src/app/api/session.js', () => ({
    requestAuthenticatedFetch: vi.fn().mockResolvedValue(
        new Response('avatar-bytes', { status: 200, headers: { 'Content-Type': 'image/jpeg' } }),
    ),
}));

import { uploadAttachment } from '../src/app/api/attachments.js';
import { requestAuthenticatedFetch } from '../src/app/api/session.js';
import { AuthenticatedImage } from '../src/app/components/AuthenticatedImage.jsx';
import { FieldControl } from '../src/app/components/fields/index.js';

function mount(vnode) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(vnode, host);
    return host;
}

afterEach(() => {
    uploadAttachment.mockClear();
    requestAuthenticatedFetch.mockClear();
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
});

describe('image attachments', () => {
    it('loads saved attachment images through authenticated fetch', async () => {
        vi.stubGlobal('URL', Object.assign(URL, {
            createObjectURL: vi.fn(() => 'blob:avatar'),
            revokeObjectURL: vi.fn(),
        }));
        const host = mount(
            <AuthenticatedImage
                src="/api/system/attachments/attachment-1/content"
                alt="Avatar"
                class="avatar"
            />,
        );
        await new Promise((resolve) => setTimeout(resolve, 0));
        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(requestAuthenticatedFetch).toHaveBeenCalledWith('/api/system/attachments/attachment-1/content');
        const image = host.querySelector('img');
        expect(image.getAttribute('src')).toBe('blob:avatar');
        expect(image.getAttribute('alt')).toBe('Avatar');
        expect(image.classList.contains('avatar')).toBe(true);
    });

    it('uploads model images as local attachments and emits the content URL', async () => {
        const onChange = vi.fn();
        const file = new File(['avatar'], 'avatar.jpg', { type: 'image/jpeg' });
        const host = mount(
            <FieldControl
                field={{ name: 'avatar_url', type: 'image' }}
                value=""
                onChange={onChange}
                context={{ modelUuid: 'model-1', record: { uuid: 'record-1' } }}
            />,
        );
        const input = host.querySelector('input[type="file"]');
        Object.defineProperty(input, 'files', { value: [file], configurable: true });

        input.dispatchEvent(new Event('change', { bubbles: true }));
        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(uploadAttachment).toHaveBeenCalledWith({
            modelUuid: 'model-1',
            recordUuid: 'record-1',
            file,
        });
        expect(onChange).toHaveBeenCalledWith(
            'avatar_url',
            '/api/system/attachments/attachment-1/content',
        );
    });
});
