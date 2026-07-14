import { useLayoutEffect, useRef } from 'preact/hooks';

import { uploadAttachment } from '../../api/attachments.js';
import { requestAuthenticatedFetch } from '../../api/session.js';
import { RICH_TEXT_TOOLBAR } from '../../views/noteEditor.js';
import { loadQuill } from '../../utils/loadQuill.js';
import { localizedValue, nextLocalizedValue } from '../../utils/ux.js';
import { safeRichTextNodes } from '../communicationPanel.jsx';
import { isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';

function nextHtmlValue(value, lang, html) {
    return nextLocalizedValue(value, lang, html);
}

function editorHtml(quill, imageUrlByPreview) {
    const clone = quill.root.cloneNode(true);
    clone.querySelectorAll('img[src]').forEach((image) => {
        const storedUrl = imageUrlByPreview.get(image.getAttribute('src'));
        if (storedUrl) image.setAttribute('src', storedUrl);
    });
    return clone.innerHTML;
}

function isAttachmentImageSource(src) {
    if (!src) return false;
    try {
        const url = new URL(src, globalThis.location?.origin ?? 'http://localhost');
        return url.pathname.startsWith('/api/system/attachments/');
    } catch {
        return false;
    }
}

async function editorPreviewHtml(html, imageUrlByPreview) {
    if (!html) return '';
    const container = document.createElement('div');
    container.innerHTML = html;
    const images = Array.from(container.querySelectorAll('img[src]'));
    await Promise.all(images.map(async (image) => {
        const storedUrl = image.getAttribute('src');
        if (!isAttachmentImageSource(storedUrl)) return;
        try {
            const response = await requestAuthenticatedFetch(storedUrl);
            if (!response.ok) throw new Error(`Unable to load image (${response.status})`);
            const previewUrl = URL.createObjectURL(await response.blob());
            imageUrlByPreview.set(previewUrl, storedUrl);
            image.setAttribute('src', previewUrl);
        } catch (error) {
            console.error('Unable to load rich text image attachment.', error);
        }
    }));
    return container.innerHTML;
}

function cleanupQuillNode(node, parent) {
    const toolbar = node?.previousElementSibling;
    if (toolbar?.classList?.contains('ql-toolbar')) {
        toolbar.remove();
    }
    parent?.querySelectorAll(':scope > .ql-toolbar').forEach((item) => item.remove());
    if (node) {
        node.innerHTML = '';
        node.classList.remove('ql-container', 'ql-snow', 'ql-disabled');
    }
}

function selectImageFile() {
    return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.className = 'hidden';
        input.addEventListener('change', () => {
            const file = input.files?.[0] ?? null;
            input.remove();
            resolve(file);
        }, { once: true });
        document.body.appendChild(input);
        input.click();
    });
}

function insertImage(quill, url) {
    const range = quill.getSelection(true);
    const index = range?.index ?? quill.getLength();
    quill.insertEmbed(index, 'image', url, 'user');
    quill.setSelection(index + 1, 0, 'silent');
}

function isAllowedImageSource(url) {
    if (typeof url !== 'string') return false;
    if (url.startsWith('blob:')) return true;
    if (url.startsWith('/api/system/attachments/')) return true;
    if (/^data:image\//i.test(url)) return true;
    return /^https?:\/\//i.test(url);
}

function registerLocalImageSources(Quill) {
    if (Quill.__webappLocalImageSourcesRegistered) return;
    const ImageFormat = Quill.import('formats/image');
    class LocalImageFormat extends ImageFormat {
        static sanitize(url) {
            return isAllowedImageSource(url) ? url : ImageFormat.sanitize(url);
        }
    }
    LocalImageFormat.blotName = ImageFormat.blotName;
    LocalImageFormat.tagName = ImageFormat.tagName;
    Quill.register(LocalImageFormat, true);
    Quill.__webappLocalImageSourcesRegistered = true;
}

export function HtmlField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const disabled = isFieldReadOnly(field, readOnly);
    const placeholder = plainText(localizedConfig(field, 'placeholder', lang));
    const displayValue = localizedValue(value, lang);
    const editorRef = useRef(null);
    const quillRef = useRef(null);
    const modelUuid = context.modelUuid ?? context.uuid;
    const recordUuid = context.record?.uuid;

    useLayoutEffect(() => {
        if (disabled || !editorRef.current) return undefined;
        const editorNode = editorRef.current;
        const editorParent = editorNode.parentElement;
        let cancelled = false;
        let quill;
        let onTextChange;
        const imageUrlByPreview = new Map();

        loadQuill().then(async (Quill) => {
            if (cancelled || !editorNode.isConnected) return;
            registerLocalImageSources(Quill);
            quill = new Quill(editorNode, {
                theme: 'snow',
                placeholder,
                modules: { toolbar: RICH_TEXT_TOOLBAR },
            });
            if (modelUuid && recordUuid) {
                quill.getModule('toolbar')?.addHandler('image', async () => {
                    const file = await selectImageFile();
                    if (!file) return;
                    try {
                        const attachment = await uploadAttachment({ modelUuid, recordUuid, file });
                        const previewUrl = URL.createObjectURL(file);
                        imageUrlByPreview.set(previewUrl, attachment.content_url);
                        insertImage(quill, previewUrl);
                    } catch (error) {
                        const message = error?.message ? `\n${error.message}` : '';
                        window.alert(`${lang === 'es' ? 'No se pudo subir la imagen.' : 'Unable to upload image.'}${message}`);
                        console.error('Unable to upload rich text image attachment.', error);
                    }
                });
            }
            quill.root.innerHTML = await editorPreviewHtml(displayValue, imageUrlByPreview);
            if (cancelled || !editorNode.isConnected) return;
            quillRef.current = quill;
            onTextChange = () => {
                const html = editorHtml(quill, imageUrlByPreview);
                onChange(field.name, nextHtmlValue(value, lang, html === '<p><br></p>' ? '' : html));
            };
            quill.on('text-change', onTextChange);
        });

        return () => {
            cancelled = true;
            quill?.off('text-change', onTextChange);
            imageUrlByPreview.forEach((_storedUrl, previewUrl) => URL.revokeObjectURL(previewUrl));
            cleanupQuillNode(editorNode, editorParent);
            quillRef.current = null;
        };
        // Quill owns the editor's content after mount; re-created only when leaving readonly mode.
    }, [disabled, modelUuid, recordUuid, lang]);

    if (disabled) {
        return (
            <div key="html-readonly" class="form-rich-text-display">
                {displayValue ? safeRichTextNodes(displayValue) : <p class="form-rich-text-placeholder">{placeholder}</p>}
            </div>
        );
    }
    return (
        <div key="html-editor" class="form-rich-text-editor-shell">
            <div class="bg-[var(--dash-surface)] rounded-lg" ref={editorRef} />
        </div>
    );
}
