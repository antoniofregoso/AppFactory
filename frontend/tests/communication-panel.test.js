import { afterEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { render } from 'preact';

vi.mock('../src/app/api/attachments.js', () => ({
  deleteAttachment: vi.fn(),
  fetchAttachmentContent: vi.fn(),
  listAttachments: vi.fn().mockResolvedValue([]),
  uploadAttachment: vi.fn(),
}));

vi.mock('../src/app/api/systemModel.js', async (importOriginal) => ({
  ...(await importOriginal()),
  fetchSystemModelByName: vi.fn(),
}));

vi.mock('../src/app/api/notes.js', () => ({
  createNote: vi.fn(),
  deleteNote: vi.fn(),
  listNotes: vi.fn().mockResolvedValue([]),
}));

vi.mock('../src/app/api/messages.js', () => ({
  createInternalMessage: vi.fn(),
  listInternalMessageRecipients: vi.fn().mockResolvedValue([
    { uuid: 'user-2', name: 'Laslo', email: 'laslo@example.com', user_type: 'HUMAN', active: true },
  ]),
}));

import { safeRichTextNodes } from '../src/app/components/communicationPanel.jsx';
import { mountForm } from './helpers/mountView.jsx';
import { deleteAttachment, fetchAttachmentContent, listAttachments, uploadAttachment } from '../src/app/api/attachments.js';
import { fetchSystemModelByName } from '../src/app/api/systemModel.js';
import { createNote, deleteNote, listNotes } from '../src/app/api/notes.js';
import { createInternalMessage } from '../src/app/api/messages.js';
import { authSignal } from '../src/app/store/authStore.js';

const styles = readFileSync('src/style.css', 'utf8');

const data = {
  model: {
    uuid: 'model-1',
    name: 'sale.order',
    label: { en: 'Orders', es: 'Órdenes' },
    schema: [
      { name: 'name', type: 'string', form: { header: 'title' } },
      { name: 'followers', type: 'one2many_followers', form: { footer: 'left' }, options: [
        { uuid: 'user-2', name: 'Laslo', email: 'laslo@example.com', user_type: 'HUMAN' },
      ] },
    ],
  },
  records: [{ uuid: 'record-1', name: 'SO-001' }],
};

afterEach(() => {
  document.body.innerHTML = '';
});

describe('communication panel', () => {
  it('shows the note author and date and allows deleting it', async () => {
    const storedNote = {
      uuid: 'note-1', content_html: '<p>Nota de seguimiento</p>',
      author_uuid: 'user-1', author_name: 'Ana Admin', created_at: '2026-07-12T18:30:00.000Z',
    };
    createNote.mockResolvedValueOnce(storedNote);
    deleteNote.mockResolvedValueOnce();
    const { cleanup } = mountForm(data, 'es');
    await vi.waitFor(() => expect(listNotes).toHaveBeenCalledWith({ modelUuid: 'model-1', recordUuid: 'record-1' }));
    document.querySelector('[data-form-tab="notes"]').click();
    document.querySelector('[data-form-tab-add="notes"]').click();
    const panel = document.querySelector('[data-form-tab-panel="notes"]');
    await vi.waitFor(() => expect(panel.querySelector('.ql-editor')).not.toBeNull());
    panel.querySelector('.ql-editor').innerHTML = '<p>Nota de seguimiento</p>';
    panel.querySelector('[data-composer-save]').click();

    await vi.waitFor(() => expect(createNote).toHaveBeenCalledWith({
      modelUuid: 'model-1', recordUuid: 'record-1', contentHtml: '<p>Nota de seguimiento</p>',
    }));
    await vi.waitFor(() => expect(panel.querySelector('[data-note-author]').textContent).toBe('Ana Admin'));
    expect(panel.querySelector('[data-note-created-at]').dateTime).not.toBe('');
    expect(panel.querySelector('[data-activity-list]').textContent).toContain('Nota de seguimiento');

    vi.stubGlobal('confirm', vi.fn().mockReturnValueOnce(true));
    panel.querySelector('[data-note-delete]').click();
    await vi.waitFor(() => expect(deleteNote).toHaveBeenCalledWith('note-1'));
    await vi.waitFor(() => expect(panel.querySelector('[data-activity-list]')).toBeNull());
    cleanup();
  });
  it('resolves the model UUID when the view payload does not include it', async () => {
    fetchSystemModelByName.mockResolvedValueOnce({ uuid: 'resolved-model-1', name: 'sale.order' });
    const dataWithoutModelUuid = { ...data, model: { ...data.model, uuid: undefined } };
    const { cleanup } = mountForm(dataWithoutModelUuid, 'es');

    await vi.waitFor(() => expect(fetchSystemModelByName).toHaveBeenCalledWith('sale.order'));
    await vi.waitFor(() => expect(listAttachments).toHaveBeenCalledWith({
      modelUuid: 'resolved-model-1', recordUuid: 'record-1',
    }));
    cleanup();
  });
  it('uploads documents and reloads persisted attachments', async () => {
    const stored = {
      uuid: 'attachment-1', original_name: 'contrato.pdf', size_bytes: 8,
      created_at: '2026-07-12T18:30:00.000Z',
      author_uuid: 'user-1', author_name: 'Ana Admin',
      content_type: 'application/pdf', content_url: '/api/system/attachments/attachment-1/content',
    };
    listAttachments.mockResolvedValueOnce([]);
    uploadAttachment.mockResolvedValueOnce(stored);
    const { cleanup } = mountForm(data, 'es');
    await vi.waitFor(() => expect(listAttachments).toHaveBeenCalledWith({ modelUuid: 'model-1', recordUuid: 'record-1' }));

    document.querySelector('[data-form-tab="documents"]').click();
    const input = document.querySelector('[data-doc-input]');
    const file = new File(['contrato'], 'contrato.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', { value: [file], configurable: true });
    input.dispatchEvent(new Event('change', { bubbles: true }));

    await vi.waitFor(() => expect(uploadAttachment).toHaveBeenCalledWith({ modelUuid: 'model-1', recordUuid: 'record-1', file }));
    await vi.waitFor(() => expect(document.querySelector('[data-activity-list]').textContent).toContain('contrato.pdf'));
    expect(document.querySelector('[data-document-created-at]').dateTime).toBe(stored.created_at);
    expect(document.querySelector('[data-document-created-at]').textContent).not.toBe('');
    expect(document.querySelector('[data-document-author]').textContent).toBe('Ana Admin');
    expect(document.querySelector('[data-document-status]')).toBeNull();
    fetchAttachmentContent.mockResolvedValueOnce(new Blob(['contrato'], { type: 'application/pdf' }));
    const viewer = { location: { href: '' }, close: vi.fn() };
    vi.spyOn(globalThis, 'open').mockReturnValueOnce(viewer);
    document.querySelector('[data-document-open]').click();
    await vi.waitFor(() => expect(fetchAttachmentContent).toHaveBeenCalledWith(stored.content_url));
    vi.stubGlobal('confirm', vi.fn().mockReturnValueOnce(true));
    deleteAttachment.mockResolvedValueOnce();
    document.querySelector('[data-document-delete]').click();
    await vi.waitFor(() => expect(deleteAttachment).toHaveBeenCalledWith('attachment-1'));
    await vi.waitFor(() => expect(document.querySelector('[data-activity-list]')).toBeNull());
    cleanup();
  });
  it('discards executable markup from rich text', () => {
    const host = document.createElement('div');
    render(safeRichTextNodes(
      '<p>Contenido seguro</p><script>window.compromised=true</script>'
      + '<img src="javascript:alert(1)" onerror="window.compromised=true">'
      + '<a href="javascript:alert(1)" onclick="window.compromised=true">enlace</a>'
    ), host);

    expect(host.textContent).toContain('Contenido seguro');
    expect(host.querySelector('script')).toBeNull();
    expect(host.querySelector('img')).toBeNull();
    expect(host.querySelector('a').hasAttribute('href')).toBe(false);
    expect(host.querySelector('[onerror], [onclick]')).toBeNull();
  });

  it('requires and displays a subject when composing a message', async () => {
    authSignal.value = { ...authSignal.value, uuid: 'admin-1', name: 'App Admin', email: 'admin@app.com' };
    createInternalMessage.mockResolvedValueOnce({
      uuid: 'message-1', subject: { es: 'Seguimiento de la propuesta' },
      message: { es: '<p>Detalle del mensaje</p>' }, fromUser: authSignal.value,
      toUsers: [{ uuid: 'user-2', name: 'Laslo' }], createdAt: '2026-07-12T18:30:00Z',
    });
    const { cleanup } = mountForm(data, 'es');
    document.querySelector('[data-form-tab="messages"]').click();
    document.querySelector('[data-form-tab-add="messages"]').click();

    const panel = document.querySelector('[data-form-tab-panel="messages"]');
    await vi.waitFor(() => expect(panel.querySelector('.ql-editor')).not.toBeNull());

    const subject = panel.querySelector('[data-message-subject]');
    const error = panel.querySelector('[data-message-subject-error]');
    const editor = panel.querySelector('.ql-editor');
    const save = panel.querySelector('[data-composer-save]');

    expect(panel.querySelector('[data-message-sender]').value).toBe('App Admin');
    expect(panel.querySelector('[data-message-sender]').readOnly).toBe(true);
    panel.querySelector('[data-message-recipient="user-2"]').click();

    expect(subject.placeholder).toBe('¿De qué trata el mensaje?');
    expect(document.activeElement).toBe(subject);

    editor.innerHTML = '<p>Detalle del mensaje</p>';
    save.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(subject.getAttribute('aria-invalid')).toBe('true');
    expect(error.classList.contains('hidden')).toBe(false);

    subject.value = 'Seguimiento de la propuesta';
    subject.dispatchEvent(new Event('input', { bubbles: true }));
    save.click();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(panel.querySelector('[data-activity-list]').textContent).toContain(
      'Seguimiento de la propuesta'
    );
    expect(panel.querySelector('[data-activity-list]').textContent).toContain(
      'Detalle del mensaje'
    );
    expect(createInternalMessage).toHaveBeenCalledWith({
      subject: 'Seguimiento de la propuesta', html: '<p>Detalle del mensaje</p>',
      senderUuid: 'admin-1', recipientUuids: ['user-2'], lang: 'es',
    });
    cleanup();
  });

  it('keeps the WhatsApp action tooltip inside the right edge', async () => {
    const { cleanup } = mountForm(data, 'en');
    const whatsappTab = document.querySelector('[data-form-tab-panel="whatsapp"]');
    const addButton = whatsappTab.querySelector('[data-form-tab-add="whatsapp"]');

    expect(addButton.dataset.tooltip).toBe('New conversation');
    expect(addButton.dataset.tooltipAlign).toBe('end');
    expect(styles).toContain('.topbar-action-btn[data-tooltip][data-tooltip-align="end"]::after');
    expect(styles).toMatch(/data-tooltip-align="end"[^}]+right:\s*0;[^}]+left:\s*auto;/s);

    document.querySelector('[data-form-tab="whatsapp"]').click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(whatsappTab.hidden).toBe(false);
    cleanup();
  });
});
