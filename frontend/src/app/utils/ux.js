
/**
 * Get the area page title in the current language.
 * @param {string} area
 * @param {string} lang
 * @param {Array} items
 * @returns {string}
 */
export function getAreaTitle(area, lang, items) {
    const item = items.find((m) => m.key === area);
    if (!item) return area;
    return lang === 'es' ? item.labelEs : item.labelEn;
}



// Color name → Tailwind badge classes (shared by status badges and pills).
export const COLOR_CLASS = {
    zinc:   'bg-zinc-100 text-zinc-600',
    red:    'bg-red-100 text-red-700',
    blue:   'bg-blue-100 text-blue-700',
    purple: 'bg-purple-100 text-purple-700',
    green:  'bg-emerald-100 text-emerald-700',
    orange: 'bg-orange-100 text-orange-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    cyan:   'bg-cyan-100 text-cyan-700',
    indigo: 'bg-indigo-100 text-indigo-700',
};
export const COLOR_FALLBACK = 'bg-zinc-100 text-zinc-700';

// Field types whose values read better right-aligned.
export const NUMERIC_TYPES = new Set(['integer', 'decimal', 'monetary', 'percentage']);

export function locale(lang) {
    return lang === 'es' ? 'es-MX' : 'en-US';
}

export function localeKey(lang = 'en', value = null) {
    const preferred = lang === 'es' ? 'es_MX' : lang === 'en' ? 'en_US' : lang;
    if (!value || typeof value !== 'object' || Array.isArray(value)) return preferred;
    if (Object.hasOwn(value, preferred)) return preferred;
    if (Object.hasOwn(value, lang)) return lang;
    return preferred;
}

/** Resolve a translated value while remaining compatible with plain strings. */
export function localizedValue(value, lang = 'en') {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        const locale = localeKey(lang, value);
        return value[locale] ?? value[lang] ?? value.en_US ?? value.en ?? value.es_MX ?? value.es ?? Object.values(value)[0] ?? '';
    }
    return value ?? '';
}

export function nextLocalizedValue(value, lang = 'en', next = '') {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        return { ...value, [localeKey(lang, value)]: next };
    }
    return next;
}

/** Resolve many-to-many tag UUIDs against the model-level tag catalog. */
export function resolveTags(value, catalog = []) {
    if (!Array.isArray(value)) return [];
    const byId = new Map((catalog ?? []).map((tag) => [String(tag?.uuid), tag]));
    return value.map((item) => {
        const id = typeof item === 'object' && item !== null ? item.uuid : item;
        return byId.get(String(id)) ?? (typeof item === 'object' ? item : null);
    }).filter(Boolean);
}
