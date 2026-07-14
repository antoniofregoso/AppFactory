import { formatDate } from '../../utils/formatters.js';
import { locale } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly, toDateInputValue } from './fieldHelpers.js';

export function DateField({ field, value, onChange, lang = 'en', readOnly = false }) {
    if (isFieldReadOnly(field, readOnly)) {
        return <span class="text-[var(--dash-text)]">{value ? formatDate(value, locale(lang)) : '—'}</span>;
    }
    return (
        <input type="date" name={field.name} class="form-control form-control--edit form-control--date" value={toDateInputValue(value)}
            aria-label={fieldLabel(field, lang)} required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, event.currentTarget.value)} />
    );
}
