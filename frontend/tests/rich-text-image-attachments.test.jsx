import { afterEach, describe, expect, it, vi } from 'vitest';
import { render } from 'preact';

const quillState = vi.hoisted(() => ({ latest: null }));

vi.mock('../src/app/api/attachments.js', () => ({
    uploadAttachment: vi.fn().mockResolvedValue({
        content_url: '/api/system/attachments/attachment-1/content',
    }),
    fetchAttachmentContent: vi.fn().mockResolvedValue(
        new Blob(['image'], { type: 'image/png' }),
    ),
}));

vi.mock('../src/app/utils/loadQuill.js', () => ({
    loadQuill: vi.fn().mockResolvedValue(class FakeQuill {
        static registeredImage = null;

        static import(name) {
            if (name !== 'formats/image') return null;
            return class ImageFormat {
                static blotName = 'image';
                static tagName = 'IMG';

                static sanitize(url) {
                    return /^(https?:|data:)/.test(url) ? url : '//:0';
                }
            };
        }

        static register(format) {
            this.registeredImage = format;
        }

        constructor(node) {
            this.root = document.createElement('div');
            this.root.className = 'ql-editor';
            node.appendChild(this.root);
            this.handlers = {};
            this.events = {};
            quillState.latest = this;
        }

        getModule(name) {
            if (name !== 'toolbar') return null;
            return {
                addHandler: (key, handler) => {
                    this.handlers[key] = handler;
                },
            };
        }

        getSelection() {
            return { index: 0 };
        }

        getLength() {
            return 0;
        }

        insertEmbed(_index, type, value) {
            if (type === 'image') {
                const src = this.constructor.registeredImage?.sanitize(value) ?? value;
                this.root.innerHTML = `<p><img src="${src}"></p>`;
                this.events['text-change']?.();
            }
        }

        setSelection() {}

        on(event, handler) {
            this.events[event] = handler;
        }

        off(event) {
            delete this.events[event];
        }
    }),
}));

import { fetchAttachmentContent, uploadAttachment } from '../src/app/api/attachments.js';
import { FieldControl } from '../src/app/components/fields/index.js';

function mount(vnode) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(vnode, host);
    return host;
}

afterEach(() => {
    uploadAttachment.mockClear();
    fetchAttachmentContent.mockClear();
    vi.unstubAllGlobals();
    quillState.latest = null;
    document.body.innerHTML = '';
});

describe('rich text image attachments', () => {
    it('uploads Quill images as attachments and inserts the content URL', async () => {
        vi.stubGlobal('URL', Object.assign(URL, {
            createObjectURL: vi.fn(() => 'blob:description-preview'),
            revokeObjectURL: vi.fn(),
        }));
        const onChange = vi.fn();
        const host = mount(
            <FieldControl
                field={{ name: 'description', type: 'html' }}
                value=""
                onChange={onChange}
                context={{ modelUuid: 'model-1', record: { uuid: 'record-1' } }}
            />,
        );
        await vi.waitFor(() => expect(host.querySelector('.ql-editor')).not.toBeNull());

        const file = new File(['image'], 'description.png', { type: 'image/png' });
        const upload = quillState.latest.handlers.image();
        const input = document.querySelector('input[type="file"]');
        Object.defineProperty(input, 'files', { value: [file], configurable: true });
        input.dispatchEvent(new Event('change', { bubbles: true }));
        await upload;

        expect(uploadAttachment).toHaveBeenCalledWith({
            modelUuid: 'model-1',
            recordUuid: 'record-1',
            file,
        });
        expect(quillState.latest.root.innerHTML).toBe('<p><img src="blob:description-preview"></p>');
        expect(onChange).toHaveBeenCalledWith(
            'description',
            { en_US: '<p><img src="/api/system/attachments/attachment-1/content"></p>' },
        );
    });

    it('shows saved attachment images as authenticated local previews while editing', async () => {
        vi.stubGlobal('URL', Object.assign(URL, {
            createObjectURL: vi.fn(() => 'blob:existing-description'),
            revokeObjectURL: vi.fn(),
        }));
        const onChange = vi.fn();
        const host = mount(
            <FieldControl
                field={{ name: 'description', type: 'html' }}
                value='<p><img src="/api/system/attachments/attachment-1/content"></p>'
                onChange={onChange}
                context={{ modelUuid: 'model-1', record: { uuid: 'record-1' } }}
            />,
        );

        await vi.waitFor(() => {
            expect(host.querySelector('.ql-editor')?.innerHTML).toBe('<p><img src="blob:existing-description"></p>');
        });
        quillState.latest.events['text-change']?.();

        expect(fetchAttachmentContent).toHaveBeenCalledWith('/api/system/attachments/attachment-1/content');
        expect(onChange).toHaveBeenCalledWith(
            'description',
            { en_US: '<p><img src="/api/system/attachments/attachment-1/content"></p>' },
        );
    });

    it('switches Quill between language tabs and preserves the other translation', async () => {
        const onChange = vi.fn();
        const host = mount(
            <FieldControl
                field={{ name: 'description', type: 'html' }}
                value={{ es_MX: '<p>Hola</p>', en_US: '<p>Hello</p>' }}
                lang="es"
                onChange={onChange}
            />,
        );

        await vi.waitFor(() => expect(host.querySelector('.ql-editor')?.innerHTML).toBe('<p>Hola</p>'));
        const tabs = host.querySelectorAll('[role="tab"]');
        expect(Array.from(tabs).map((tab) => tab.textContent)).toEqual(['ES●', 'EN●']);

        tabs[1].click();
        await vi.waitFor(() => expect(host.querySelector('.ql-editor')?.innerHTML).toBe('<p>Hello</p>'));

        quillState.latest.root.innerHTML = '<p>Hello updated</p>';
        quillState.latest.events['text-change']?.();
        expect(onChange).toHaveBeenCalledWith('description', {
            es_MX: '<p>Hola</p>',
            en_US: '<p>Hello updated</p>',
        });
    });

    it('loads short locale keys used by existing records', async () => {
        const host = mount(
            <FieldControl
                field={{ name: 'message', type: 'html' }}
                value={{ es: '<p>Mensaje original</p>' }}
                lang="es"
                onChange={() => {}}
            />,
        );

        await vi.waitFor(() => expect(host.querySelector('.ql-editor')?.innerHTML).toBe('<p>Mensaje original</p>'));
        expect(host.querySelector('[role="tab"]').textContent).toBe('ES●');
    });
});
