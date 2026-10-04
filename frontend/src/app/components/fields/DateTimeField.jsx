import { formatDateTime } from '../../utils/formatters.js';
import { locale } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly, toDateTimeInputValue } from './fieldHelpers.js';
import { TaskScheduleField } from './TaskScheduleField.jsx';

export function DateTimeField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    if (context?.name === 'system.task' && field?.name === 'date_due') {
        return <TaskScheduleField field={field} value={value} onChange={onChange} lang={lang} readOnly={readOnly} context={context} />;
    }
    if (isFieldReadOnly(field, readOnly)) {
        return <span class="text-[var(--dash-text)]">{value ? formatDateTime(value, locale(lang)) : '—'}</span>;
    }
    return (
        <input type="datetime-local" name={field.name} class="form-control form-control--edit form-control--date"
            value={toDateTimeInputValue(value)} aria-label={fieldLabel(field, lang)}
            required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, event.currentTarget.value)} />
    );
}
