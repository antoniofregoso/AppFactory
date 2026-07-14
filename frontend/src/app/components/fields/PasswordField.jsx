import { fieldLabel, hasValue, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';

function maskValue(value) {
    if (!hasValue(value)) return '—';
    return '••••••••';
}

function isEncodedSecret(value) {
    return typeof value === 'string' && /^\$(argon2(?:id|i|d)?|2[aby]|scrypt)\$/i.test(value);
}

export function PasswordField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const disabled = isFieldReadOnly(field, readOnly);
    const label = fieldLabel(field, lang);

    if (disabled) {
        return <span class="form-password-display text-[var(--dash-text)]" aria-label={label}>{maskValue(value)}</span>;
    }

    const storedEncodedSecret = isEncodedSecret(value);
    const displayValue = storedEncodedSecret ? '' : value ?? '';
    const placeholder = storedEncodedSecret
        ? maskValue(value)
        : plainText(localizedConfig(field, 'placeholder', lang));

    return (
        <div class="form-password-control">
            <input
                type="password"
                name={field.name}
                class="form-control form-control--edit form-password-input"
                value={displayValue}
                aria-label={label}
                placeholder={placeholder}
                required={field?.form?.required === true && !storedEncodedSecret}
                autocomplete="new-password"
                onInput={(event) => onChange(field.name, event.currentTarget.value)}
            />
        </div>
    );
}
