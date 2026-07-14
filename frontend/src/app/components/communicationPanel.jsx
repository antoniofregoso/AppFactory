import { h, render } from 'preact';
import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';

import {
    faEnvelope, faFileLines, faFloppyDisk, faNoteSticky, faPaperPlane, faPlus,
    faTrash, faWhatsapp, faXmark,
} from './icon.js';
import { AuthenticatedImage } from './AuthenticatedImage.jsx';
import { RICH_TEXT_TOOLBAR } from '../views/noteEditor.js';
import { loadQuill } from '../utils/loadQuill.js';
import { deleteAttachment, fetchAttachmentContent, listAttachments, uploadAttachment } from '../api/attachments.js';
import { fetchSystemModelByName } from '../api/systemModel.js';
import { createNote, deleteNote, listNotes } from '../api/notes.js';
import { createInternalMessage, listInternalMessageRecipients } from '../api/messages.js';
import { authSignal } from '../store/authStore.js';

const COPY = {
    notes: {
        label: { es: 'Notas', en: 'Notes' },
        add: { es: 'Agregar nota', en: 'Add note' },
        empty: { es: 'Aún no hay notas.', en: 'No notes yet.' },
        placeholder: { es: 'Escribe una nota...', en: 'Write a note...' },
        save: { es: 'Guardar nota', en: 'Save note' },
        delete: { es: 'Borrar nota', en: 'Delete note' },
        unknownAuthor: { es: 'Usuario desconocido', en: 'Unknown user' },
    },
    whatsapp: {
        label: { es: 'WhatsApp', en: 'WhatsApp' },
        add: { es: 'Nueva conversación', en: 'New conversation' },
        empty: { es: 'Sin conversaciones de WhatsApp.', en: 'No WhatsApp conversations.' },
        placeholder: { es: 'Escribe un mensaje...', en: 'Write a message...' },
        save: { es: 'Enviar', en: 'Send' },
    },
    messages: {
        label: { es: 'Mensajes', en: 'Messages' },
        add: { es: 'Nuevo mensaje', en: 'New message' },
        empty: { es: 'Sin mensajes.', en: 'No messages.' },
        placeholder: { es: 'Escribe un mensaje...', en: 'Write a message...' },
        save: { es: 'Enviar mensaje', en: 'Send message' },
        subject: { es: 'Asunto', en: 'Subject' },
        subjectPlaceholder: { es: '¿De qué trata el mensaje?', en: 'What is this message about?' },
        subjectRequired: { es: 'Escribe un asunto para continuar.', en: 'Add a subject to continue.' },
        sender: { es: 'Remitente', en: 'Sender' },
        recipients: { es: 'Destinatarios', en: 'Recipients' },
        recipientSearch: { es: 'Buscar usuarios...', en: 'Search users...' },
        recipientsRequired: { es: 'Selecciona al menos un destinatario.', en: 'Select at least one recipient.' },
        loadingRecipients: { es: 'Cargando usuarios...', en: 'Loading users...' },
        noRecipients: { es: 'No se encontraron usuarios.', en: 'No users found.' },
        sendError: { es: 'No se pudo enviar el mensaje.', en: 'Unable to send the message.' },
    },
    documents: {
        label: { es: 'Documentos', en: 'Documents' },
        add: { es: 'Subir documento', en: 'Upload document' },
        empty: { es: 'Sin documentos adjuntos.', en: 'No documents attached.' },
        uploading: { es: 'Adjuntando archivos...', en: 'Uploading files...' },
        uploadError: { es: 'No se pudieron adjuntar los archivos.', en: 'Unable to upload the files.' },
        delete: { es: 'Borrar documento', en: 'Delete document' },
    },
};

const TAB_ORDER = ['notes', 'whatsapp', 'messages', 'documents'];
const TAB_ICONS = { notes: faNoteSticky, whatsapp: faWhatsapp, messages: faEnvelope, documents: faFileLines };
const SAFE_TAGS = new Set(['a', 'blockquote', 'br', 'em', 'h1', 'h2', 'h3', 'img', 'li', 'ol', 'p', 's', 'span', 'strong', 'u', 'ul']);
const DROP_CONTENT_TAGS = new Set(['iframe', 'object', 'script', 'style', 'svg', 'template']);

function copy(tab, key, lang) {
    return COPY[tab][key]?.[lang] ?? COPY[tab][key]?.en ?? '';
}

function Icon({ definition, class: className = '' }) {
    const [width, height, , , paths] = definition.icon;
    const pathList = Array.isArray(paths) ? paths : [paths];
    return (
        <svg class={className} viewBox={`0 0 ${width} ${height}`} aria-hidden="true" focusable="false">
            {pathList.map((path, index) => <path d={path} key={index} />)}
        </svg>
    );
}

function safeUrl(value, image = false) {
    const url = String(value ?? '').trim();
    if (/^https?:/i.test(url)) return url;
    if (image && /^\/api\/system\/attachments\/[^/]+\/content$/i.test(url)) return url;
    if (image && /^data:image\/(?:gif|jpe?g|png|webp);base64,/i.test(url)) return url;
    return '';
}

function nodeToVnode(node, key) {
    if (node.nodeType === 3) return node.textContent;
    if (node.nodeType !== 1) return null;

    const tag = node.tagName.toLowerCase();
    if (DROP_CONTENT_TAGS.has(tag)) return null;
    const children = Array.from(node.childNodes, (child, index) => nodeToVnode(child, `${key}-${index}`));
    if (!SAFE_TAGS.has(tag)) return children;

    const props = { key };
    const quillClasses = Array.from(node.classList ?? []).filter((name) => /^ql-[a-z0-9-]+$/i.test(name));
    if (quillClasses.length) props.class = quillClasses.join(' ');
    if (tag === 'li' && /^(?:bullet|checked|unchecked|ordered)$/.test(node.dataset.list ?? '')) {
        props['data-list'] = node.dataset.list;
    }
    if (tag === 'a') {
        const href = safeUrl(node.getAttribute('href'));
        if (href) props.href = href;
        props.rel = 'noopener noreferrer';
        if (node.getAttribute('target') === '_blank') props.target = '_blank';
    }
    if (tag === 'img') {
        const src = safeUrl(node.getAttribute('src'), true);
        if (!src) return null;
        props.alt = node.getAttribute('alt') ?? '';
        if (src.startsWith('/api/system/attachments/')) {
            return h(AuthenticatedImage, { ...props, src });
        }
        props.src = src;
    }
    return h(tag, props, children);
}

export function safeRichTextNodes(html) {
    const documentNode = new DOMParser().parseFromString(String(html ?? ''), 'text/html');
    return Array.from(documentNode.body.childNodes, (node, index) => nodeToVnode(node, `rich-${index}`));
}

function ComposerButtons({ tab, lang, onCancel, onSave, saveIcon = faFloppyDisk }) {
    const cancel = lang === 'es' ? 'Cancelar' : 'Cancel';
    return (
        <div class="flex justify-end gap-1">
            <button type="button" data-composer-cancel class="topbar-action-btn" aria-label={cancel} data-tooltip={cancel} onClick={onCancel}>
                <Icon definition={faXmark} class="topbar-action-icon" />
            </button>
            <button type="button" data-composer-save class="topbar-action-btn" aria-label={copy(tab, 'save', lang)} data-tooltip={copy(tab, 'save', lang)} onClick={onSave}>
                <Icon definition={saveIcon} class="topbar-action-icon" />
            </button>
        </div>
    );
}

function RichComposer({ tab, lang, onClose, onSave, currentUser, users = [], usersLoading = false }) {
    const editorRef = useRef(null);
    const quillRef = useRef(null);
    const subjectRef = useRef(null);
    const [subject, setSubject] = useState('');
    const [subjectInvalid, setSubjectInvalid] = useState(false);
    const [recipientSearch, setRecipientSearch] = useState('');
    const [selectedRecipients, setSelectedRecipients] = useState([]);
    const [recipientsInvalid, setRecipientsInvalid] = useState(false);
    const [sendError, setSendError] = useState(false);

    useLayoutEffect(() => {
        let cancelled = false;

        loadQuill().then((Quill) => {
            if (cancelled || !editorRef.current) return;
            quillRef.current = new Quill(editorRef.current, {
                theme: 'snow',
                placeholder: copy(tab, 'placeholder', lang),
                modules: { toolbar: RICH_TEXT_TOOLBAR },
            });
            if (tab === 'messages') subjectRef.current?.focus();
            else quillRef.current.focus();
        });

        return () => {
            cancelled = true;
            quillRef.current = null;
        };
    }, [lang, tab]);

    const save = async () => {
        const value = (subjectRef.current?.value ?? subject).trim();
        if (tab === 'messages' && !value) {
            setSubjectInvalid(true);
            subjectRef.current?.focus();
            return;
        }
        if (tab === 'messages' && selectedRecipients.length === 0) {
            setRecipientsInvalid(true);
            return;
        }
        const html = quillRef.current?.root?.innerHTML ?? '';
        if (!html || html === '<p><br></p>') return;
        try {
            await onSave(tab === 'messages' ? {
                subject: value,
                html,
                senderUuid: currentUser?.uuid,
                recipientUuids: selectedRecipients,
            } : html);
            onClose();
        } catch {
            setSendError(true);
        }
    };

    const recipientOptions = users.filter((user) => {
        if (!user?.uuid || String(user.uuid) === String(currentUser?.uuid) || user.user_type === 'SYSTEM') return false;
        const query = recipientSearch.trim().toLocaleLowerCase();
        return !query || `${user.name ?? ''} ${user.display_name ?? ''} ${user.email ?? ''}`.toLocaleLowerCase().includes(query);
    });

    return (
        <div data-quill-composer class="border-b border-[var(--dash-border)] p-4 flex flex-col gap-3">
            {tab === 'messages' && <>
                <label class="flex flex-col gap-1.5 text-xs font-semibold text-[var(--dash-text-muted)]">
                    <span>{copy(tab, 'sender', lang)}</span>
                    <input type="text" data-message-sender readOnly value={currentUser?.name || currentUser?.email || ''}
                        class="form-control bg-[var(--dash-bg)] text-[var(--dash-text-muted)]" />
                </label>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-semibold text-[var(--dash-text-muted)]" for="message-recipient-search">{copy(tab, 'recipients', lang)}</label>
                    <input id="message-recipient-search" type="search" data-message-recipient-search value={recipientSearch}
                        placeholder={copy(tab, 'recipientSearch', lang)} class="form-control form-control--edit"
                        onInput={(event) => setRecipientSearch(event.currentTarget.value)} />
                    <div class="flex max-h-32 flex-wrap gap-2 overflow-y-auto" data-message-recipient-options>
                        {recipientOptions.map((user) => {
                            const selected = selectedRecipients.includes(String(user.uuid));
                            return <button type="button" data-message-recipient={user.uuid} aria-pressed={String(selected)}
                                class={`rounded-full border px-2.5 py-1 text-xs ${selected ? 'border-[var(--dash-accent)] bg-[var(--dash-accent-soft)] text-[var(--dash-accent)]' : 'border-[var(--dash-border)] text-[var(--dash-text)]'}`}
                                onClick={() => {
                                    setRecipientsInvalid(false);
                                    setSelectedRecipients((current) => selected
                                        ? current.filter((uuid) => uuid !== String(user.uuid))
                                        : [...current, String(user.uuid)]);
                                }} key={user.uuid}>{user.display_name || user.name || user.email}</button>;
                        })}
                        {usersLoading && <span class="text-xs text-[var(--dash-text-muted)]">{copy(tab, 'loadingRecipients', lang)}</span>}
                        {!usersLoading && recipientOptions.length === 0 && <span data-message-no-recipients class="text-xs text-[var(--dash-text-muted)]">{copy(tab, 'noRecipients', lang)}</span>}
                    </div>
                    {recipientsInvalid && <span role="alert" data-message-recipients-error class="text-xs text-[var(--dash-danger)]">{copy(tab, 'recipientsRequired', lang)}</span>}
                </div>
            </>}
            {tab === 'messages' && (
                <label class="flex min-w-0 flex-col gap-1.5 text-xs font-semibold text-[var(--dash-text-muted)]">
                    <span>{copy(tab, 'subject', lang)}</span>
                    <input ref={subjectRef} type="text" maxLength="160" data-message-subject
                        class="box-border w-full min-w-0 rounded-lg border border-[var(--dash-border)] bg-[var(--dash-surface)] px-3 py-2 text-sm font-normal text-[var(--dash-text)] outline-none transition-colors placeholder:text-[var(--dash-text-soft)] focus:border-[var(--dash-accent)] focus:ring-2 focus:ring-[var(--dash-accent-soft)]"
                        placeholder={copy(tab, 'subjectPlaceholder', lang)} aria-required="true"
                        aria-invalid={String(subjectInvalid)} value={subject}
                        onInput={(event) => { setSubject(event.currentTarget.value); setSubjectInvalid(false); }} />
                    <span class={subjectInvalid ? 'font-normal text-[var(--dash-danger)]' : 'hidden font-normal text-[var(--dash-danger)]'} data-message-subject-error>
                        {copy(tab, 'subjectRequired', lang)}
                    </span>
                </label>
            )}
            <div ref={editorRef} data-quill-el class="bg-[var(--dash-surface)] rounded-lg" />
            {sendError && <span role="alert" data-message-send-error class="text-xs text-[var(--dash-danger)]">{copy(tab, 'sendError', lang)}</span>}
            <ComposerButtons tab={tab} lang={lang} onCancel={onClose} onSave={save} />
        </div>
    );
}

function TextComposer({ lang, onClose, onSave }) {
    const [text, setText] = useState('');
    const inputRef = useRef(null);
    useEffect(() => inputRef.current?.focus(), []);
    const save = () => {
        const value = text.trim();
        if (!value) return;
        onSave(value);
        onClose();
    };
    return (
        <div data-text-composer class="border-b border-[var(--dash-border)] p-4 flex flex-col gap-3">
            <textarea ref={inputRef} data-text-input rows="3" value={text} onInput={(event) => setText(event.currentTarget.value)}
                placeholder={copy('whatsapp', 'placeholder', lang)}
                class="w-full resize-none rounded-lg border border-[var(--dash-border)] bg-[var(--dash-surface)] px-3 py-2 text-sm text-[var(--dash-text)] placeholder:text-[var(--dash-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--dash-accent)]" />
            <ComposerButtons tab="whatsapp" lang={lang} onCancel={onClose} onSave={save} saveIcon={faPaperPlane} />
        </div>
    );
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatAttachmentDate(value, lang) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat(lang === 'es' ? 'es-MX' : 'en-US', {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(date);
}

async function openDocument(item) {
    const inline = item.content_type === 'application/pdf' || item.content_type?.startsWith('image/');
    const viewer = inline ? globalThis.open?.('', '_blank') : null;
    try {
        const blob = await fetchAttachmentContent(item.content_url);
        const objectUrl = URL.createObjectURL(blob);
        if (viewer) {
            viewer.location.href = objectUrl;
        } else {
            const link = document.createElement('a');
            link.href = objectUrl;
            link.download = item.original_name ?? 'attachment';
            link.click();
        }
        globalThis.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (error) {
        viewer?.close();
        console.error('Unable to open record attachment.', error);
        globalThis.alert?.('No se pudo abrir el documento.');
    }
}

function ActivityItem({ tab, item, lang, onDelete }) {
    if (tab === 'documents') {
        const attachedAt = formatAttachmentDate(item.created_at, lang);
        return (
        <div class="flex items-center gap-3">
            <span class="shrink-0 text-[var(--dash-text-muted)]"><Icon definition={faFileLines} class="topbar-action-icon" /></span>
            <button type="button" data-document-open class="min-w-0 flex-1 truncate text-left font-medium text-[var(--dash-accent)] hover:underline"
                onClick={() => { void openDocument(item); }}>{item.original_name ?? item.name}</button>
            <span class="shrink-0 text-right text-xs text-[var(--dash-text-muted)]">
                <span class="block">{formatSize(item.size_bytes ?? item.size)}</span>
                {item.author_name && <span class="block font-medium text-[var(--dash-text)]" data-document-author>{item.author_name}</span>}
                {attachedAt && <time class="block" data-document-created-at dateTime={item.created_at}>{attachedAt}</time>}
            </span>
            <button type="button" data-document-delete class="topbar-action-btn shrink-0"
                aria-label={copy('documents', 'delete', lang)} data-tooltip={copy('documents', 'delete', lang)}
                onClick={() => { void onDelete(item); }}><Icon definition={faTrash} class="topbar-action-icon" /></button>
        </div>
        );
    }
    if (tab === 'messages') return (
        <article class="min-w-0">
            <h4 class="truncate text-sm font-semibold text-[var(--dash-text)]">{item.subject}</h4>
            <div class="ql-editor mt-1 p-0 text-sm text-[var(--dash-text-muted)]">{safeRichTextNodes(item.html)}</div>
        </article>
    );
    if (tab === 'notes') {
        const createdAt = formatAttachmentDate(item.created_at, lang);
        return <article>
            <div class="mb-2 flex items-start justify-between gap-3">
                <div class="min-w-0 text-xs text-[var(--dash-text-muted)]">
                    <span class="font-medium text-[var(--dash-text)]" data-note-author>{item.author_name || copy('notes', 'unknownAuthor', lang)}</span>
                    {createdAt && <time class="ml-2" data-note-created-at dateTime={item.created_at}>{createdAt}</time>}
                </div>
                <button type="button" data-note-delete class="topbar-action-btn shrink-0"
                    aria-label={copy('notes', 'delete', lang)} data-tooltip={copy('notes', 'delete', lang)}
                    onClick={() => { void onDelete(item); }}><Icon definition={faTrash} class="topbar-action-icon" /></button>
            </div>
            <div class="ql-editor p-0">{safeRichTextNodes(item.content_html ?? item.html)}</div>
        </article>;
    }
    return item;
}

function TabPanel({ tab, lang, items, onAdd, onDeleteItem, onUploadDocuments, onDeleteDocument, hidden, documentStatus, currentUser, users, usersLoading }) {
    const [composing, setComposing] = useState(false);
    const inputRef = useRef(null);
    const addItems = (newItems) => onAdd(tab, newItems);
    const open = () => tab === 'documents' ? inputRef.current?.click() : setComposing(true);
    return (
        <div data-form-tab-panel={tab} hidden={hidden}>
            <div class="flex items-center justify-between border-b border-[var(--dash-border)] px-4 py-2">
                <span class="text-xs font-medium text-[var(--dash-text-muted)]">{copy(tab, 'label', lang)}</span>
                <button type="button" class="topbar-action-btn" aria-label={copy(tab, 'add', lang)} data-tooltip={copy(tab, 'add', lang)}
                    data-tooltip-align="end" data-form-tab-add={tab} onClick={open}>
                    <Icon definition={faPlus} class="topbar-action-icon" />
                </button>
            </div>
            {tab === 'documents' && <input ref={inputRef} type="file" multiple data-doc-input class="hidden"
                onChange={(event) => {
                    const files = Array.from(event.currentTarget.files ?? []);
                    event.currentTarget.value = '';
                    if (files.length) void onUploadDocuments(files);
                }} />}
            {tab === 'documents' && documentStatus && (
                <div role="status" data-document-status class={`border-b border-[var(--dash-border)] px-4 py-2 text-xs ${documentStatus === 'error' ? 'text-[var(--dash-danger)]' : 'text-[var(--dash-text-muted)]'}`}>
                    {copy('documents', documentStatus === 'error' ? 'uploadError' : 'uploading', lang)}
                </div>
            )}
            {composing && (tab === 'notes' || tab === 'messages') &&
                <RichComposer tab={tab} lang={lang} onClose={() => setComposing(false)}
                    currentUser={currentUser} users={users} usersLoading={usersLoading}
                    onSave={(item) => tab === 'notes' ? onAdd(tab, [item]) : onAdd(tab, [item])} />}
            {composing && tab === 'whatsapp' &&
                <TextComposer lang={lang} onClose={() => setComposing(false)} onSave={(item) => addItems([item])} />}
            {items.length === 0 ? (
                <div data-note-empty class="min-h-48 px-4 py-5 text-sm text-[var(--dash-text-muted)]">{copy(tab, 'empty', lang)}</div>
            ) : (
                <ul data-activity-list class="divide-y divide-[var(--dash-border)]">
                    {items.map((item, index) => <li class="px-4 py-3 text-sm text-[var(--dash-text)]" key={item.uuid ?? index}>
                        <ActivityItem tab={tab} item={item} lang={lang} onDelete={tab === 'documents' ? onDeleteDocument : onDeleteItem} />
                    </li>)}
                </ul>
            )}
        </div>
    );
}

export function CommunicationPanel({ lang = 'en', modelUuid, modelName, recordUuid, users = [] }) {
    const [activeTab, setActiveTab] = useState('notes');
    const [items, setItems] = useState(() => Object.fromEntries(TAB_ORDER.map((tab) => [tab, []])));
    const [documentStatus, setDocumentStatus] = useState('');
    const [resolvedModelUuid, setResolvedModelUuid] = useState(modelUuid ?? '');
    const currentUser = authSignal.value;
    const [messageUsers, setMessageUsers] = useState(users);
    const [messageUsersLoading, setMessageUsersLoading] = useState(true);
    const addItems = (tab, additions) => setItems((current) => ({ ...current, [tab]: [...additions, ...current[tab]] }));
    useEffect(() => {
        let cancelled = false;
        setMessageUsersLoading(true);
        listInternalMessageRecipients()
            .then((records) => {
                if (!cancelled) setMessageUsers(records);
            })
            .catch((error) => {
                if (!cancelled) setMessageUsers(users);
                console.error('Unable to load internal message recipients.', error);
            })
            .finally(() => {
                if (!cancelled) setMessageUsersLoading(false);
            });
        return () => { cancelled = true; };
    }, [users]);
    useEffect(() => {
        let cancelled = false;
        if (modelUuid) {
            setResolvedModelUuid(modelUuid);
            return;
        }
        setResolvedModelUuid('');
        if (!modelName) return;
        fetchSystemModelByName(modelName)
            .then((model) => {
                if (!cancelled) setResolvedModelUuid(model?.uuid ?? '');
            })
            .catch((error) => console.error('Unable to resolve the attachment model.', error));
        return () => { cancelled = true; };
    }, [modelName, modelUuid]);
    useEffect(() => {
        let cancelled = false;
        if (!resolvedModelUuid || !recordUuid) return;
        listAttachments({ modelUuid: resolvedModelUuid, recordUuid })
            .then((documents) => {
                if (!cancelled) setItems((current) => ({ ...current, documents }));
            })
            .catch((error) => console.error('Unable to load record attachments.', error));
        listNotes({ modelUuid: resolvedModelUuid, recordUuid })
            .then((notes) => {
                if (!cancelled) setItems((current) => ({ ...current, notes }));
            })
            .catch((error) => console.error('Unable to load record notes.', error));
        return () => { cancelled = true; };
    }, [resolvedModelUuid, recordUuid]);
    const uploadDocuments = async (files) => {
        if (!resolvedModelUuid || !recordUuid) {
            setDocumentStatus('error');
            return;
        }
        setDocumentStatus('uploading');
        try {
            const documents = await Promise.all(files.map((file) => uploadAttachment({ modelUuid: resolvedModelUuid, recordUuid, file })));
            addItems('documents', documents);
            setDocumentStatus('');
        } catch (error) {
            setDocumentStatus('error');
            console.error('Unable to upload record attachments.', error);
        }
    };
    const removeDocument = async (document) => {
        const question = lang === 'es'
            ? `¿Borrar "${document.original_name}"? Esta acción no se puede deshacer.`
            : `Delete "${document.original_name}"? This action cannot be undone.`;
        if (!globalThis.confirm?.(question)) return;
        try {
            await deleteAttachment(document.uuid);
            setItems((current) => ({
                ...current,
                documents: current.documents.filter((item) => item.uuid !== document.uuid),
            }));
        } catch (error) {
            console.error('Unable to delete record attachment.', error);
            globalThis.alert?.(lang === 'es' ? 'No se pudo borrar el documento.' : 'Unable to delete the document.');
        }
    };
    const saveNote = async (contentHtml) => {
        if (!resolvedModelUuid || !recordUuid) {
            globalThis.alert?.(lang === 'es' ? 'No se pudo identificar el registro.' : 'Unable to identify the record.');
            return;
        }
        try {
            const note = await createNote({ modelUuid: resolvedModelUuid, recordUuid, contentHtml });
            addItems('notes', [note]);
        } catch (error) {
            console.error('Unable to create record note.', error);
            globalThis.alert?.(lang === 'es' ? 'No se pudo guardar la nota.' : 'Unable to save the note.');
        }
    };
    const sendMessage = async ({ subject, html, senderUuid, recipientUuids }) => {
        try {
            const message = await createInternalMessage({ subject, html, senderUuid, recipientUuids, lang });
            addItems('messages', [{
                uuid: message.uuid,
                subject: message.subject?.[lang] ?? subject,
                html: message.message?.[lang] ?? html,
                from_user: message.fromUser,
                to_users: message.toUsers,
                created_at: message.createdAt ?? message.date,
            }]);
        } catch (error) {
            console.error('Unable to send internal message.', error);
            throw error;
        }
    };
    const removeItem = async (tab, item) => {
        const question = lang === 'es'
            ? '¿Borrar esta nota? Esta acción no se puede deshacer.'
            : 'Delete this note? This action cannot be undone.';
        if (!globalThis.confirm?.(question)) return;
        try {
            if (tab === 'notes') await deleteNote(item.uuid);
            setItems((current) => ({
                ...current,
                [tab]: current[tab].filter((currentItem) => currentItem.uuid !== item.uuid),
            }));
        } catch (error) {
            console.error('Unable to delete record note.', error);
            globalThis.alert?.(lang === 'es' ? 'No se pudo borrar la nota.' : 'Unable to delete the note.');
        }
    };
    return (
        <aside class="rounded-xl border border-[var(--dash-border)] bg-[var(--dash-surface)] shadow-[var(--dash-shadow)]" data-form-activity>
            <div class="grid border-b border-[var(--dash-border)] px-3 py-2" style={{ gridTemplateColumns: `repeat(${TAB_ORDER.length}, minmax(0, 1fr))` }}>
                {TAB_ORDER.map((tab) => (
                    <div class={`form-activity-tab ${activeTab === tab ? 'form-activity-tab--active' : ''}`} key={tab}>
                        <button type="button" class="topbar-action-btn" aria-label={copy(tab, 'label', lang)} aria-pressed={String(activeTab === tab)}
                            data-tooltip={copy(tab, 'label', lang)} data-form-tab={tab} onClick={() => setActiveTab(tab)}>
                            <Icon definition={TAB_ICONS[tab]} class="topbar-action-icon" />
                        </button>
                    </div>
                ))}
            </div>
            {TAB_ORDER.map((tab) => (
                <TabPanel tab={tab} lang={lang} items={items[tab]}
                    onAdd={(itemTab, additions) => itemTab === 'notes'
                        ? saveNote(additions[0])
                        : itemTab === 'messages' ? sendMessage(additions[0]) : addItems(itemTab, additions)}
                    onUploadDocuments={uploadDocuments}
                    onDeleteItem={(item) => removeItem(tab, item)} onDeleteDocument={removeDocument}
                    documentStatus={documentStatus} currentUser={currentUser} users={messageUsers} usersLoading={messageUsersLoading}
                    hidden={activeTab !== tab} key={tab} />
            ))}
        </aside>
    );
}

export function mountCommunicationPanel(container, lang) {
    if (!container) return () => {};
    render(<CommunicationPanel lang={lang} />, container);
    return () => render(null, container);
}
