import { formatCurrency } from '../../utils/formatters.js';
import { locale } from '../../utils/ux.js';
import { fieldLabel, hasValue, isFieldReadOnly } from './fieldHelpers.js';

export function MonetaryField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const currency = field.currency ?? 'MXN';
    if (isFieldReadOnly(field, readOnly)) {
        return (
            <span class="tabular-nums text-[var(--dash-text)]">
                {hasValue(value) ? formatCurrency(Number(value), locale(lang), currency) : '—'}
            </span>
        );
    }
    return (
        <input type="number" name={field.name} step="0.01" class="form-control form-control--edit" value={value ?? ''}
            aria-label={fieldLabel(field, lang)} required={field?.form?.required === true}
            onInput={(event) => onChange(field.name, event.currentTarget.value)} />
    );
}
