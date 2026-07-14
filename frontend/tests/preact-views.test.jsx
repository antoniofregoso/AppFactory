import { afterEach, describe, expect, it } from 'vitest';
import { render } from 'preact';

import { CalendarView, FormView, KanbanView, ListView, toCalendarEvents } from '../src/app/views/index.js';

const schema = [
    { name: 'name', type: 'string', label: { en: 'Name' }, kanban: { header: 'title' }, list: { column: 0, order: true }, form: { header: 'title' }, calendar: { title: true } },
    { name: 'status', type: 'selection', label: { en: 'Status' }, list: { column: 1 } },
    { name: 'starts_at', type: 'datetime', label: { en: 'Start' }, calendar: { startDate: true }, form: { leftColumn: 0 } },
    { name: 'color', type: 'color', label: { en: 'Color' }, selection_values: [
        { value: 'Red', hex: '#dc2626', label: { en_US: 'Red' } },
        { value: 'Blue', hex: '#2563eb', label: { en_US: 'Blue' } },
    ] },
];
const today = new Date();
const localDay = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
const data = {
    model: {
        name: 'task', label: { en: 'Tasks' }, schema, groupBy: 'status',
        status: [{ value: 'todo', en: 'To do', color: 'zinc' }, { value: 'done', en: 'Done', color: 'green' }],
    },
    records: [
        { uuid: '2', name: 'Second', status: 'done', starts_at: `${localDay}T10:00:00` },
        { uuid: '1', name: 'First', status: 'todo', starts_at: `${localDay}T09:00:00` },
    ],
};

function mount(vnode) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(vnode, host);
    return host;
}

afterEach(() => {
    if (document.body.firstElementChild) render(null, document.body.firstElementChild);
    document.body.innerHTML = '';
});

describe('Preact schema views', () => {
    it('groups Kanban cards declaratively', () => {
        const host = mount(<KanbanView data={data} lang="en" />);
        expect(host.querySelectorAll('[data-group-value]')).toHaveLength(2);
        expect(host.querySelector('[data-group-value="todo"]').textContent).toContain('First');
    });

    it('renders a related user name and avatar in Kanban and List views', () => {
        const userField = {
            name: 'user_id',
            type: 'many2one_avatar',
            model: 'user.user',
            label: { en: 'User' },
            kanban: { header: 'title' },
            list: { column: 1 },
            form: { header: 'title', readonly: true },
        };
        const user = {
            uuid: 'user-1',
            name: 'Ana Admin',
            avatar: 'https://example.com/ana.jpg',
            model: 'user.user',
        };
        const userLogData = {
            model: { name: 'user.log', label: { en: 'User Logs' }, schema: [userField] },
            records: [{ uuid: 'log-1', user_id: user }],
        };

        const kanbanHost = mount(<KanbanView data={userLogData} lang="en" />);
        const card = kanbanHost.querySelector('[data-uuid="log-1"]');
        expect(card.textContent).toContain('Ana Admin');
        expect(card.querySelector('img').getAttribute('src')).toBe(user.avatar);
        render(null, kanbanHost);
        kanbanHost.remove();

        const listHost = mount(<ListView data={userLogData} lang="en" />);
        const row = listHost.querySelector('[data-list-rows] [data-uuid="log-1"]');
        expect(row.textContent).toContain('Ana Admin');
        expect(row.querySelector('img').getAttribute('src')).toBe(user.avatar);
    });

    it('removes mutation controls from readonly model views', () => {
        const readonlyData = {
            ...data,
            model: { ...data.model, readonly: true },
        };

        const kanbanHost = mount(<KanbanView data={readonlyData} lang="en" />);
        expect(kanbanHost.querySelector('[data-create-open]')).toBeNull();
        expect(kanbanHost.querySelector('.js-kanban-drag-handle')).toBeNull();
        render(null, kanbanHost);
        kanbanHost.remove();

        const listHost = mount(<ListView data={readonlyData} lang="en" />);
        expect(listHost.querySelector('[data-create-open]')).toBeNull();
        expect(listHost.querySelector('.js-list-drag-handle')).toBeNull();
        expect(listHost.querySelector('.js-list-row-select')).toBeNull();
        render(null, listHost);
        listHost.remove();

        const formHost = mount(<FormView data={readonlyData} lang="en" />);
        expect(formHost.querySelector('[data-create-open]')).toBeNull();
        expect(formHost.querySelector('[data-form-edit]')).toBeNull();
        expect(formHost.querySelector('[data-form-save]')).toBeNull();
        expect(formHost.querySelector('[data-form-root]').dataset.formMode).toBe('readonly');
    });

    it('opens a color-grid picker in the Kanban card footer', async () => {
        const host = mount(<KanbanView data={data} lang="en" />);
        const card = host.querySelector('[data-uuid="1"]');
        card.querySelector('[data-kanban-color-picker] > button').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        const picker = host.querySelector('[data-uuid="1"] [role="radiogroup"]');
        expect(picker).not.toBeNull();
        expect(picker.querySelectorAll('[role="radio"]')).toHaveLength(2);
        expect(picker.querySelector('[aria-label="Blue"]').style.backgroundColor).toBe('#2563eb');
    });

    it('sorts List rows through component state', async () => {
        const host = mount(<ListView data={data} lang="en" />);
        host.querySelector('.js-list-sort').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(host.querySelector('[data-list-rows] tr').textContent).toContain('First');
    });

    it('switches Form fields from readonly to editable', async () => {
        const host = mount(<FormView data={data} lang="en" />);
        expect(host.querySelector('[data-form-root]').dataset.formMode).toBe('readonly');
        host.querySelector('[data-form-edit]').click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        expect(host.querySelector('[data-form-root]').dataset.formMode).toBe('edit');
        expect(host.querySelector('input[name="name"]').value).toBe('Second');
    });

    it('renders Calendar events from schema metadata', () => {
        const host = mount(<CalendarView data={data} lang="en" />);
        expect(host.querySelectorAll('[data-event-id]')).toHaveLength(2);
        expect(host.querySelector('[data-event-id="1"]').textContent).toContain('First');
    });

    it('uses a 30 minute calendar fallback and omits invalid starts', () => {
        const [event] = toCalendarEvents({ ...data, records: [
            { uuid: 'valid', name: 'Valid', starts_at: `${localDay}T12:00:00` },
            { uuid: 'invalid', name: 'Invalid', starts_at: 'not-a-date' },
        ] });
        expect(event.endsAt.getTime() - event.startsAt.getTime()).toBe(30 * 60_000);
    });

    it('renders localized form actions and record navigation', () => {
        const host = mount(<FormView data={data} lang="es" options={{ recordModel: 'task', recordUuid: '1' }} />);
        expect(host.querySelector('[data-form-save]').getAttribute('aria-label')).toBe('Guardar');
        expect(host.querySelector('[data-form-nav="previous"]').getAttribute('href')).toContain('/task/2');
        expect(host.querySelector('[data-form-nav="next"]').disabled).toBe(true);
    });
});
