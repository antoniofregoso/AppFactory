import { fieldLabel, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';
import { localizedValue, nextLocalizedValue } from '../../utils/ux.js';
import { TaskRecurrenceValue } from './TaskScheduleField.jsx';

export function StringField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const displayValue = localizedValue(value, lang);
    if (isFieldReadOnly(field, readOnly)) {
        if (context?.name === 'system.task' && field?.name === 'recurrence') {
            return <TaskRecurrenceValue value={value} lang={lang} />;
        }
        return <span class="text-[var(--dash-text)]">{displayValue ? String(displayValue) : '—'}</span>;
    }
    return (
        <input type="text" name={field.name} class="form-control form-control--edit" value={displayValue ?? ''}
            aria-label={fieldLabel(field, lang)} placeholder={plainText(localizedConfig(field, 'placeholder', lang))}
            required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, nextLocalizedValue(value, lang, event.currentTarget.value))} />
    );
}
