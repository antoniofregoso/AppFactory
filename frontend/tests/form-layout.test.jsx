import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateSystemModelRecord } from '../src/app/api/systemModel.js';
import { createEmptyRecord, getFormLayout } from '../src/app/views/formLayout.js';
import { mountForm } from './helpers/mountView.jsx';

vi.mock('../src/app/api/systemModel.js', () => ({
    createSystemModelRecord: vi.fn(),
    deleteSystemModelRecord: vi.fn(),
    fetchSystemModelByName: vi.fn().mockResolvedValue(null),
    updateSystemModelRecord: vi.fn().mockResolvedValue(true),
}));

vi.mock('../src/app/api/messages.js', () => ({
    createInternalMessage: vi.fn(),
    listInternalMessageRecipients: vi.fn().mockResolvedValue([]),
}));

const schema = [
    { name: 'avatar', type: 'image', label: { en: 'Image' }, form: { header: 'image' } },
    { name: 'name', type: 'string', label: { en: 'Order' }, form: { header: 'title', required: true } },
    { name: 'customer', type: 'many2one', label: { en: 'Customer' }, form: { header: 'subtitle' } },
    { name: 'second', type: 'string', label: { en: 'Second' }, form: { leftColumn: 1 } },
    { name: 'first', type: 'string', label: { en: 'First' }, form: { leftColumn: 0, readonly: true } },
    { name: 'right', type: 'string', label: { en: 'Right' }, form: { rightColumn: 0 } },
    { name: 'description', type: 'html', label: { en: 'Description' }, form: { tab: 0, help: { en: 'Internal notes' } } },
    { name: 'ignored', type: 'string', label: { en: 'Ignored' } },
];
const data = {
    model: { name: 'sale.order', label: { en: 'Orders' }, schema },
    records: [{ uuid: '1', avatar: '/avatar.jpg', name: 'SO-001', customer: { name: 'ACME' }, first: 'A', second: 'B', right: 'C', description: '', ignored: 'Hidden' }],
};

afterEach(() => {
    vi.restoreAllMocks();
    updateSystemModelRecord.mockClear();
    document.body.innerHTML = '';
});

describe('schema-driven form layout', () => {
    it('uses defaults declared by the schema for a new record', () => {
        expect(createEmptyRecord([
            { name: 'status', type: 'status_badge', default: 'Pending' },
            { name: 'priority', type: 'selection', default: 'Low' },
            { name: 'color', type: 'color', default: 'Zinc' },
        ])).toMatchObject({ status: 'Pending', priority: 'Low', color: 'Zinc' });
    });

    it('persists selected followers through the record update', async () => {
        const setTimeoutSpy = vi.spyOn(globalThis, 'setTimeout');
        const clearTimeoutSpy = vi.spyOn(globalThis, 'clearTimeout');
        const follower = { uuid: 'user-2', name: 'Ana', user_type: 'HUMAN' };
        const followerData = {
            model: {
                ...data.model,
                schema: [...schema, {
                    name: 'followers', type: 'one2many_followers',
                    label: { en: 'Followers' }, form: { footer: 'left' }, options: [follower],
                }],
            },
            records: [{ ...data.records[0], followers: [] }],
        };
        const { cleanup } = mountForm(followerData, 'en');
        document.querySelector('[data-form-edit]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        document.querySelector('button[aria-label="Ana"]').click();

        await vi.waitFor(() => expect(updateSystemModelRecord).toHaveBeenCalledWith({
            model: 'sale.order', recordUuid: '1', values: { followers: [follower] },
        }));
        await vi.waitFor(() => expect(document.querySelector('[data-follower-status]').textContent).toBe('Saved'));
        const statusTimerIndex = setTimeoutSpy.mock.calls.findIndex(([, delay]) => delay === 1500);
        const statusTimer = setTimeoutSpy.mock.results[statusTimerIndex]?.value;
        cleanup();
        expect(statusTimerIndex).toBeGreaterThanOrEqual(0);
        expect(clearTimeoutSpy).toHaveBeenCalledWith(statusTimer);
    });
    it('places and orders fields in the four supported areas', () => {
        const layout = getFormLayout(schema);
        expect(layout.header.image.name).toBe('avatar');
        expect(layout.header.title.name).toBe('name');
        expect(layout.leftColumn.map(({ field }) => field.name)).toEqual(['first', 'second']);
        expect(layout.rightColumn.map(({ field }) => field.name)).toEqual(['right']);
        expect(layout.tabs[0].fields[0].field.name).toBe('description');
    });

    it('renders configured fields and omits unplaced fields', () => {
        const { host, cleanup } = mountForm(data);
        expect(host.querySelector('[data-form-header="image"] img').getAttribute('src')).toBe('/avatar.jpg');
        expect(host.querySelector('[data-form-field="first"]')).not.toBeNull();
        expect(host.querySelector('[data-form-field="description"]')).not.toBeNull();
        expect(host.textContent).not.toContain('Hidden');
        cleanup();
    });

    it('keeps schema-readonly controls disabled in edit mode', async () => {
        const { host, cleanup } = mountForm(data);
        host.querySelector('[data-form-edit]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(host.querySelector('[data-form-field="first"] input')).toBeNull();
        expect(host.querySelector('[data-form-field="second"] input').disabled).toBe(false);
        cleanup();
    });

    it('persists edited form values and keeps multilingual object shape', async () => {
        const localizedData = {
            ...data,
            records: [{
                ...data.records[0],
                name: { en_US: 'Order', es_MX: 'Orden' },
            }],
        };
        const { host, cleanup } = mountForm(localizedData, 'es');
        host.querySelector('[data-form-edit]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        const input = host.querySelector('input[name="name"]');
        input.value = 'Orden actualizada';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        host.querySelector('[data-form-save]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(updateSystemModelRecord).toHaveBeenCalledWith({
            model: 'sale.order',
            recordUuid: '1',
            values: { name: { en_US: 'Order', es_MX: 'Orden actualizada' } },
        });
        expect(host.querySelector('[data-form-root]').dataset.formMode).toBe('readonly');
        cleanup();
    });

    it('saves a recurrence edit as one atomic field change', async () => {
        const taskData = {
            model: {
                name: 'system.task', label: { es: 'Tareas' },
                schema: [
                    { name: 'title', type: 'string', label: { es: 'Título' }, form: { header: 'title' } },
                    { name: 'date_due', type: 'datetime', label: { es: 'Fecha límite' }, form: { leftColumn: 1 } },
                    { name: 'recurrence', type: 'string', label: { es: 'Recurrencia' } },
                ],
            },
            records: [{ uuid: 'task-1', title: 'Reporte', date_due: '2026-10-09T12:00:00', recurrence: 'weekly' }],
        };
        const { host, cleanup } = mountForm(taskData, 'es');
        host.querySelector('[data-form-edit]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        const recurrence = host.querySelector('select[aria-label="Recurrencia"]');
        recurrence.value = 'daily';
        recurrence.dispatchEvent(new Event('change', { bubbles: true }));
        host.querySelector('[data-form-save]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(updateSystemModelRecord).toHaveBeenCalledWith({
            model: 'system.task', recordUuid: 'task-1', values: { recurrence: 'daily' },
        });
        cleanup();
    });
});
