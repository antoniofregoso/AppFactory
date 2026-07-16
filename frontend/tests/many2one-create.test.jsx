import { afterEach, describe, expect, it, vi } from 'vitest';
import { act } from 'preact/test-utils';
import { render } from 'preact';

const api = vi.hoisted(() => ({ create: vi.fn(), fetchView: vi.fn() }));

vi.mock('../src/app/api/systemModel.js', () => ({
    createSystemModelRecord: api.create,
    fetchSystemModelView: api.fetchView,
}));

import { CreateModal } from '../src/app/views/ViewPrimitives.jsx';

const customerView = {
    model: {
        name: 'sale.customer',
        label: { es: 'Cliente', en: 'Customer' },
        schema: [
            { name: 'name', type: 'string', label: { es: 'Nombre' }, form: { header: 'title', required: true } },
            { name: 'email', type: 'string', label: { es: 'Correo' }, form: { leftColumn: 0 } },
        ],
    },
    records: [
        { uuid: 'customer-1', name: 'Acme' },
        { uuid: 'customer-2', name: 'Zenith', code: 'ZEN' },
    ],
};

const orderView = {
    model: {
        name: 'sale.order',
        label: { es: 'Orden de venta', en: 'Sales order' },
        schema: [{
            name: 'customer_id',
            type: 'many2one',
            model: 'sale.customer',
            label: { es: 'Cliente' },
            form: { leftColumn: 0, required: true },
        }],
    },
    records: [],
};

afterEach(() => {
    render(null, document.body);
    document.body.innerHTML = '';
    vi.clearAllMocks();
});

describe('many2one searchable creation', () => {
    it('searches options, creates a missing relation, selects it, and saves its UUID', async () => {
        api.fetchView.mockResolvedValue(customerView);
        api.create.mockImplementation(({ model }) => Promise.resolve(model === 'sale.customer'
            ? { uuid: 'customer-3', name: 'Nueva SA' }
            : { uuid: 'order-1' }));
        const host = document.createElement('div');
        document.body.appendChild(host);
        act(() => render(<CreateModal data={orderView} lang="es" open onClose={() => {}} />, host));

        await vi.waitFor(() => expect(api.fetchView).toHaveBeenCalledWith({ model: 'sale.customer' }));
        const picker = host.querySelector('[data-many2one-picker="customer_id"]');
        const search = picker.querySelector('input[type="search"]');
        act(() => search.focus());
        search.value = 'zen';
        act(() => search.dispatchEvent(new Event('input', { bubbles: true })));
        await vi.waitFor(() => expect(picker.querySelectorAll('[role="option"]')).toHaveLength(1));
        expect(picker.querySelector('[role="option"]').textContent).toContain('Zenith');

        search.value = 'Nueva SA';
        act(() => search.dispatchEvent(new Event('input', { bubbles: true })));
        act(() => picker.querySelector('[data-many2one-add="customer_id"]').click());

        await vi.waitFor(() => expect(host.querySelectorAll('[data-form-modal]')).toHaveLength(2));
        const relatedName = [...host.querySelectorAll('input[name="name"]')].at(-1);
        expect(relatedName.value).toBe('Nueva SA');
        const saveButtons = [...host.querySelectorAll('button[aria-label="Guardar"]')];
        act(() => saveButtons.at(-1).click());

        await vi.waitFor(() => expect(api.create).toHaveBeenCalledWith({
            model: 'sale.customer',
            values: { name: 'Nueva SA' },
        }));
        await vi.waitFor(() => expect(search.value).toBe('Nueva SA'));

        act(() => host.querySelector('button[aria-label="Guardar"]').click());
        await vi.waitFor(() => expect(api.create).toHaveBeenLastCalledWith({
            model: 'sale.order',
            values: {
                customer_id: { uuid: 'customer-3', name: 'Nueva SA', model: 'sale.customer' },
            },
        }));
    });
});
