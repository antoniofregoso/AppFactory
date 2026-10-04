import { useMemo } from 'preact/hooks';

import { faArrowsRotate, icon } from '../icon.js';
import { formatDateTime } from '../../utils/formatters.js';
import { locale } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly, toDateTimeInputValue } from './fieldHelpers.js';

function localDateTimeValue(date) {
    const offset = date.getTimezoneOffset() * 60_000;
    return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function quickDueDate(days, now = new Date()) {
    const date = new Date(now);
    date.setDate(date.getDate() + days);
    date.setHours(23, 59, 0, 0);
    return localDateTimeValue(date);
}

function capitalize(value) {
    return value ? `${value[0].toLocaleUpperCase()}${value.slice(1)}` : value;
}

export function recurrenceOptions(lang = 'en', now = new Date()) {
    const language = lang === 'es' ? 'es-MX' : 'en-US';
    const weekday = capitalize(new Intl.DateTimeFormat(language, { weekday: 'long' }).format(now));
    const month = capitalize(new Intl.DateTimeFormat(language, { month: 'long' }).format(now));
    const day = now.getDate();
    if (lang === 'es') return [
        ['daily', 'Diario'],
        ['weekly', `Semanal en ${weekday}`],
        ['biweekly', `Cada 2 semanas en ${weekday}`],
        ['monthly', `Mensual el ${day}`],
        ['quarterly', `Cada 3 meses el ${day}`],
        ['yearly', `Anual en ${month} el ${day}`],
        ['weekdays', 'Solo días hábiles'],
        ['daily_after_completion', 'Diario después de completar'],
        ['every_3_days_after_completion', 'Cada 3 días después de completar'],
        ['weekly_after_completion', 'Semanal después de completar'],
        ['monthly_after_completion', 'Mensual después de completar'],
        ['custom', 'Recurrencia personalizada'],
    ];
    return [
        ['daily', 'Daily'],
        ['weekly', `Weekly on ${weekday}`],
        ['biweekly', `Every 2 weeks on ${weekday}`],
        ['monthly', `Monthly on the ${day}`],
        ['quarterly', `Every 3 months on the ${day}`],
        ['yearly', `Yearly in ${month} on the ${day}`],
        ['weekdays', 'Weekdays only'],
        ['daily_after_completion', 'Daily after completion'],
        ['every_3_days_after_completion', 'Every 3 days after completion'],
        ['weekly_after_completion', 'Weekly after completion'],
        ['monthly_after_completion', 'Monthly after completion'],
        ['custom', 'Custom recurrence'],
    ];
}

function recurrenceKey(value) {
    return String(value ?? '').startsWith('custom:') ? 'custom' : String(value ?? '');
}

function recurrenceLabel(value, options) {
    if (!value) return '';
    if (String(value).startsWith('custom:')) {
        return String(value).slice(7).trim() || options.find(([key]) => key === 'custom')?.[1] || '';
    }
    return options.find(([key]) => key === value)?.[1] ?? String(value);
}

export function TaskScheduleField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const options = useMemo(() => recurrenceOptions(lang), [lang]);
    const recurrence = context?.record?.recurrence ?? '';
    const labels = lang === 'es'
        ? { today: 'Hoy', tomorrow: 'Mañana', nextWeek: 'Próxima semana', recurrence: 'Recurrencia', custom: 'Describe la recurrencia' }
        : { today: 'Today', tomorrow: 'Tomorrow', nextWeek: 'Next week', recurrence: 'Recurrence', custom: 'Describe the recurrence' };

    if (isFieldReadOnly(field, readOnly)) {
        return <div class="task-schedule-readonly">
            <span class="text-[var(--dash-text)]">{value ? formatDateTime(value, locale(lang)) : '—'}</span>
            {recurrence && <span class="task-recurrence-summary">
                <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faArrowsRotate, 'task-recurrence-icon') }} />
                {recurrenceLabel(recurrence, options)}
            </span>}
        </div>;
    }

    const chooseRecurrence = (event) => {
        const next = event.currentTarget.value;
        onChange('recurrence', next === 'custom' ? 'custom:' : next);
    };
    return <div class="task-schedule" data-task-schedule>
        <input type="datetime-local" name={field.name} class="form-control form-control--edit form-control--date"
            value={toDateTimeInputValue(value)} aria-label={fieldLabel(field, lang)} required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, event.currentTarget.value)} />
        <div class="task-schedule-actions" role="group" aria-label={lang === 'es' ? 'Atajos de fecha límite' : 'Due date shortcuts'}>
            <button type="button" class="task-schedule-chip" onClick={() => onChange(field.name, quickDueDate(0))}>{labels.today}</button>
            <button type="button" class="task-schedule-chip" onClick={() => onChange(field.name, quickDueDate(1))}>{labels.tomorrow}</button>
            <button type="button" class="task-schedule-chip" onClick={() => onChange(field.name, quickDueDate(7))}>{labels.nextWeek}</button>
            <label class={`task-recurrence-select ${recurrence ? 'task-recurrence-select--active' : ''}`}>
                <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faArrowsRotate, 'task-recurrence-icon') }} />
                <span class="sr-only">{labels.recurrence}</span>
                <select value={recurrenceKey(recurrence)} aria-label={labels.recurrence} onChange={chooseRecurrence}>
                    <option value="">{labels.recurrence}</option>
                    {options.map(([key, label]) => <option value={key} key={key}>{label}</option>)}
                </select>
            </label>
        </div>
        {recurrenceKey(recurrence) === 'custom' && <input type="text" class="form-control form-control--edit task-recurrence-custom"
            value={String(recurrence).slice(7)} placeholder={labels.custom} aria-label={labels.custom} maxLength={120}
            onInput={(event) => onChange('recurrence', `custom:${event.currentTarget.value}`)} />}
    </div>;
}
