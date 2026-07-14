import { fieldLabel, hasValue, isFieldReadOnly } from './fieldHelpers.js';

export function IntegerField({ field, value, onChange, lang = 'en', readOnly = false }) {
    if (isFieldReadOnly(field, readOnly)) {
        return <span class="tabular-nums text-[var(--dash-text)]">{hasValue(value) ? value : '—'}</span>;
    }
    return (
        <input type="number" name={field.name} step="1" class="form-control form-control--edit" value={value ?? ''}
            aria-label={fieldLabel(field, lang)} required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, event.currentTarget.value)} />
    );
}
