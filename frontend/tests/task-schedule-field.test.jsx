import { afterEach, describe, expect, it, vi } from 'vitest';
import { render } from 'preact';

import { FieldControl } from '../src/app/components/fields/index.js';
import { quickDueDate, recurrenceOptions } from '../src/app/components/fields/TaskScheduleField.jsx';

function mount(vnode) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(vnode, host);
    return host;
}

afterEach(() => {
    document.body.innerHTML = '';
});

describe('task due date controls', () => {
    const field = {
        name: 'date_due',
        type: 'datetime',
        label: { es: 'Fecha límite', en: 'Due date' },
        form: { leftColumn: 1 },
    };

    it('renders the three due date shortcuts and the recurrence selector only for tasks', () => {
        const host = mount(<FieldControl field={field} value="" onChange={() => {}} lang="es"
            context={{ name: 'system.task', record: { recurrence: '' } }} />);

        const buttons = [...host.querySelectorAll('.task-schedule-chip')];
        expect(buttons.map((button) => button.textContent)).toEqual(['Hoy', 'Mañana', 'Próxima semana']);
        expect(host.querySelector('select[aria-label="Recurrencia"]')).not.toBeNull();
        expect(host.querySelectorAll('select option')).toHaveLength(13);

        const regularHost = mount(<FieldControl field={field} value="" onChange={() => {}} lang="es"
            context={{ name: 'another.model', record: {} }} />);
        expect(regularHost.querySelector('[data-task-schedule]')).toBeNull();
    });

    it('emits shortcut dates and a selected recurrence rule', () => {
        const onChange = vi.fn();
        const host = mount(<FieldControl field={field} value="" onChange={onChange} lang="es"
            context={{ name: 'system.task', record: { recurrence: '' } }} />);

        host.querySelector('.task-schedule-chip').click();
        expect(onChange).toHaveBeenCalledWith('date_due', expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/));

        const select = host.querySelector('select');
        select.value = 'weekdays';
        select.dispatchEvent(new Event('change', { bubbles: true }));
        expect(onChange).toHaveBeenCalledWith('recurrence', 'weekdays');
    });

    it('supports a persisted custom recurrence', () => {
        const onChange = vi.fn();
        const host = mount(<FieldControl field={field} value="" onChange={onChange} lang="es"
            context={{ name: 'system.task', record: { recurrence: 'custom:cada último viernes' } }} />);
        const custom = host.querySelector('.task-recurrence-custom');

        expect(host.querySelector('select').value).toBe('custom');
        expect(custom.value).toBe('cada último viernes');
        custom.value = 'cada 10 días';
        custom.dispatchEvent(new Event('input', { bubbles: true }));
        expect(onChange).toHaveBeenCalledWith('recurrence', 'custom:cada 10 días');
    });

    it('builds dynamic weekday, day and month labels', () => {
        const now = new Date(2026, 9, 4, 9, 30);
        const labels = Object.fromEntries(recurrenceOptions('es', now));

        expect(labels.weekly).toBe('Semanal en Domingo');
        expect(labels.monthly).toBe('Mensual el 4');
        expect(labels.yearly).toBe('Anual en Octubre el 4');
        expect(quickDueDate(1, now)).toBe('2026-10-05T23:59');
    });
});
