import { afterEach, describe, expect, it, vi } from 'vitest';
import { act } from 'preact/test-utils';
import { render } from 'preact';

const api = vi.hoisted(() => ({ update: vi.fn(), refresh: vi.fn() }));
vi.mock('../src/app/api/systemModel.js', () => ({
  createSystemModelRecord: vi.fn(), deleteSystemModelRecord: vi.fn(),
  fetchSystemModelByName: vi.fn().mockResolvedValue(null), updateSystemModelRecord: api.update,
}));
vi.mock('../src/app/api/pendingCounts.js', () => ({ refreshPendingCounts: api.refresh }));
vi.mock('../src/app/api/attachments.js', () => ({ listAttachments: vi.fn().mockResolvedValue([]), uploadAttachment: vi.fn() }));
vi.mock('../src/app/api/notes.js', () => ({ listNotes: vi.fn().mockResolvedValue([]), createNote: vi.fn(), deleteNote: vi.fn() }));
vi.mock('../src/app/api/messages.js', () => ({
  listInternalMessageRecipients: vi.fn().mockResolvedValue([]), createInternalMessage: vi.fn(),
}));

import { FormView } from '../src/app/views/FormView.jsx';
import { authSignal } from '../src/app/store/authStore.js';

const sender = { uuid: 'sender-1', name: 'Laslo', email: 'laslo@example.com', model: 'user.user' };
const recipient = { uuid: 'admin-1', name: 'App Admin', email: 'admin@app.com', model: 'user.user' };
const data = {
  model: {
    name: 'system.message', label: { es: 'Mensajes', en: 'Messages' },
    schema: [
      { name: 'subject', type: 'string', label: { es: 'Asunto' }, form: { header: 'title', required: true } },
      { name: 'from_user_id', type: 'many2one', label: { es: 'Remitente' }, form: { header: 'subtitle', readonly: true, required: true } },
      { name: 'to_users', type: 'many2many_pills', model: 'user.user', options: [sender, recipient], label: { es: 'Destinatarios' }, form: { leftColumn: 0, required: true } },
      { name: 'status', type: 'status_badge', label: { es: 'Estado' }, selection_values: [{ value: 'Sent', es: 'Enviado' }], form: { rightColumn: 0, required: true, readonly: true } },
      { name: 'message', type: 'html', label: { es: 'Mensaje' }, form: { leftColumn: 1, required: true } },
    ],
  },
  records: [{
    uuid: 'message-1', status: 'Sent', date: '2026-07-12T18:30:00.000Z', subject: { es: 'Prueba' }, message: { es: '<p>Hola</p>' },
    from_user_id: sender, to_users: [recipient],
  }],
};

afterEach(() => {
  document.body.innerHTML = '';
  vi.clearAllMocks();
});

describe('message detail', () => {
  it('marks a received message read and opens a prefilled reply', async () => {
    authSignal.value = { ...authSignal.value, uuid: 'admin-1', name: 'App Admin', email: 'admin@app.com', isAuthenticated: true };
    api.update.mockResolvedValue({ status: 'Read' });
    api.refresh.mockResolvedValue({ messages: 0, notifications: 0 });
    const host = document.createElement('div');
    document.body.appendChild(host);
    act(() => render(<FormView data={data} lang="es" options={{ recordModel: 'system.message', recordUuid: 'message-1' }} />, host));

    await vi.waitFor(() => expect(api.update).toHaveBeenCalledWith({
      model: 'system.message', recordUuid: 'message-1', values: { status: 'Read' },
    }));
    await vi.waitFor(() => expect(api.refresh).toHaveBeenCalled());

    act(() => host.querySelector('[data-message-reply]').click());
    await vi.waitFor(() => expect(host.querySelector('[data-form-modal]')).not.toBeNull());
    await vi.waitFor(() => expect(host.querySelector('[data-form-modal] [name="subject"]').value).toBe('Re: Prueba'));
    expect(host.querySelector('[data-form-modal] button[aria-label="Enviar"]')).not.toBeNull();
    expect(host.querySelector('[data-form-modal] [data-form-field="status"]').textContent).toContain('Enviado');
    expect(host.querySelector('[data-form-modal]').textContent).toContain('Laslo');
    await vi.waitFor(() => expect(host.querySelector('[data-form-modal] .ql-editor')?.innerHTML).toContain('Mensaje original'));
    expect(host.querySelector('[data-form-modal] .ql-editor').innerHTML).toContain('Hola');
    expect(host.querySelector('[data-form-modal] .ql-editor').innerHTML).toContain('Laslo');
  });
});
