import { afterEach, describe, expect, it, vi } from 'vitest';
import { render } from 'preact';
import { act } from 'preact/test-utils';

vi.mock('../src/app/api/systemModel.js', () => ({
  createSystemModelRecord: vi.fn(),
}));

import { CreateModal } from '../src/app/views/ViewPrimitives.jsx';
import { createSystemModelRecord } from '../src/app/api/systemModel.js';

const data = {
  model: {
    name: 'user.user',
    label: { es: 'Usuarios', en: 'Users' },
    schema: [
      { name: 'name', type: 'string', label: { es: 'Nombre', en: 'Name' }, form: { header: 'title', required: true } },
      { name: 'email', type: 'string', label: { es: 'Correo electrónico', en: 'Email' }, form: { header: 'subtitle', required: true } },
      { name: 'password', type: 'password', label: { es: 'Contraseña', en: 'Password' }, form: { rightColumn: 0, required: true } },
      { name: 'user_type', type: 'selection', label: { es: 'Tipo de usuario', en: 'User type' },
        selection_values: [{ value: 'HUMAN', es: 'Humano', en: 'Human' }], form: { rightColumn: 1, required: true } },
    ],
  },
};

afterEach(() => {
  render(null, document.body);
  document.body.innerHTML = '';
});

describe('create modal required fields', () => {
  it('lists required user fields and keeps the modal open with field errors', async () => {
    const onClose = vi.fn();
    const host = document.createElement('div');
    document.body.appendChild(host);
    act(() => render(<CreateModal data={data} lang="es" open onClose={onClose} />, host));

    expect(host.querySelector('[data-required-fields]').textContent).toContain('Nombre');
    expect(host.querySelector('[data-required-fields]').textContent).toContain('Correo electrónico');
    expect(host.querySelector('[data-required-fields]').textContent).toContain('Contraseña');
    expect(host.querySelector('[data-required-fields]').textContent).toContain('Tipo de usuario');
    expect(host.querySelectorAll('.form-required-mark')).toHaveLength(4);

    await new Promise((resolve) => setTimeout(resolve, 0));
    act(() => host.querySelector('button[aria-label="Guardar"]').click());

    await vi.waitFor(() => expect(host.querySelectorAll('[data-field-error]')).toHaveLength(4));
    expect(onClose).not.toHaveBeenCalled();
    expect(host.querySelector('[data-form-modal]')).not.toBeNull();
  });

  it('persists a valid user and closes only after the API confirms it', async () => {
    const onClose = vi.fn();
    createSystemModelRecord.mockResolvedValueOnce({
      uuid: 'user-2', name: 'Ana Admin', email: 'ana@example.com', user_type: 'HUMAN', active: true,
      followers: [{ uuid: 'admin-1', name: 'Admin' }],
    });
    const host = document.createElement('div');
    document.body.appendChild(host);
    act(() => render(<CreateModal data={data} lang="es" open onClose={onClose} />, host));
    await new Promise((resolve) => setTimeout(resolve, 0));

    for (const [name, value] of Object.entries({ name: 'Ana Admin', email: 'ana@example.com', password: 'password123', user_type: 'HUMAN' })) {
      const input = host.querySelector(`[name="${name}"]`);
      input.value = value;
      act(() => input.dispatchEvent(new Event(input.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true })));
    }
    act(() => host.querySelector('button[aria-label="Guardar"]').click());

    await vi.waitFor(() => expect(createSystemModelRecord).toHaveBeenCalledWith({
      model: 'user.user',
      values: { name: 'Ana Admin', email: 'ana@example.com', password: 'password123', user_type: 'HUMAN' },
    }));
    await vi.waitFor(() => expect(onClose).toHaveBeenCalledOnce());
  });
});
