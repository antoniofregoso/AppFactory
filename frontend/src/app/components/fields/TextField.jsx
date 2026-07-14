import { fieldLabel, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';
import { localizedValue, nextLocalizedValue } from '../../utils/ux.js';

export function TextField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const displayValue = localizedValue(value, lang);
    if (isFieldReadOnly(field, readOnly)) {
        return <p class="whitespace-pre-wrap text-[var(--dash-text)]">{displayValue ? String(displayValue) : '—'}</p>;
    }
    return (
        <textarea name={field.name} class="form-control form-control--edit form-control--textarea" value={displayValue ?? ''}
            aria-label={fieldLabel(field, lang)} placeholder={plainText(localizedConfig(field, 'placeholder', lang))}
            required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, nextLocalizedValue(value, lang, event.currentTarget.value))} />
    );
}
