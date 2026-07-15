import { useEffect, useMemo, useState } from 'preact/hooks';

import { localizedValue } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';

const DEFAULT_LOCALES = ['es_MX', 'en_US'];
const LOCALE_LABELS = {
    es_MX: 'ES',
    en_US: 'EN',
};

function canonicalLocale(lang = 'en') {
    const normalized = String(lang).replace('-', '_').toLowerCase();
    if (normalized.startsWith('es')) return 'es_MX';
    if (normalized.startsWith('en')) return 'en_US';
    return String(lang).replace('-', '_');
}

function configuredLocales(field, value) {
    const configured = field?.form?.languages ?? field?.languages;
    const candidates = Array.isArray(configured) && configured.length
        ? configured
        : [...DEFAULT_LOCALES, ...Object.keys(value && typeof value === 'object' ? value : {})];
    return [...new Set(candidates.map(canonicalLocale))];
}

function localeLabel(locale) {
    return LOCALE_LABELS[locale] ?? locale.split('_')[0].toUpperCase();
}

export function StringI18nField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const locales = useMemo(() => configuredLocales(field, value), [field, value]);
    const preferredLocale = canonicalLocale(lang);
    const [activeLocale, setActiveLocale] = useState(
        locales.includes(preferredLocale) ? preferredLocale : locales[0],
    );

    useEffect(() => {
        if (!locales.includes(activeLocale)) {
            setActiveLocale(locales.includes(preferredLocale) ? preferredLocale : locales[0]);
        }
    }, [activeLocale, locales, preferredLocale]);

    if (isFieldReadOnly(field, readOnly)) {
        const displayValue = localizedValue(value, lang);
        return <span class="text-[var(--dash-text)]">{displayValue ? String(displayValue) : '—'}</span>;
    }

    const translations = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    const placeholder = plainText(localizedConfig(field, 'placeholder', activeLocale));
    return (
        <div class="form-i18n-control" data-i18n-field={field.name}>
            <div class="form-i18n-tabs" role="tablist" aria-label={`${fieldLabel(field, lang)} languages`}>
                {locales.map((locale) => (
                    <button
                        key={locale}
                        type="button"
                        role="tab"
                        aria-selected={activeLocale === locale}
                        class={`form-i18n-tab ${activeLocale === locale ? 'form-i18n-tab--active' : ''}`}
                        onClick={() => setActiveLocale(locale)}
                    >
                        {localeLabel(locale)}
                        {translations[locale] ? <span class="form-i18n-complete" aria-label="translated">●</span> : null}
                    </button>
                ))}
            </div>
            <input
                type="text"
                name={field.name}
                class="form-control form-control--edit form-i18n-input"
                value={translations[activeLocale] ?? ''}
                aria-label={`${fieldLabel(field, lang)} (${localeLabel(activeLocale)})`}
                placeholder={placeholder}
                required={field?.form?.required === true && activeLocale === preferredLocale}
                onInput={(event) => onChange(field.name, {
                    ...translations,
                    [activeLocale]: event.currentTarget.value,
                })}
            />
        </div>
    );
}
