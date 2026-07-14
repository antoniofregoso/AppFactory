import { fieldLabel, isFieldReadOnly } from './fieldHelpers.js';
import { localizedValue } from '../../utils/ux.js';

const DEFAULT_COLORS = [
    { value: 'Zinc', label: { es_MX: 'Zinc', en_US: 'Zinc' }, hex: '#71717a' },
    { value: 'Red', label: { es_MX: 'Rojo', en_US: 'Red' }, hex: '#dc2626' },
    { value: 'Blue', label: { es_MX: 'Azul', en_US: 'Blue' }, hex: '#2563eb' },
    { value: 'Purple', label: { es_MX: 'Morado', en_US: 'Purple' }, hex: '#9333ea' },
    { value: 'Green', label: { es_MX: 'Verde', en_US: 'Green' }, hex: '#16a34a' },
    { value: 'Orange', label: { es_MX: 'Naranja', en_US: 'Orange' }, hex: '#ea580c' },
    { value: 'Yellow', label: { es_MX: 'Amarillo', en_US: 'Yellow' }, hex: '#ca8a04' },
    { value: 'Cyan', label: { es_MX: 'Cian', en_US: 'Cyan' }, hex: '#0891b2' },
    { value: 'Indigo', label: { es_MX: 'Indigo', en_US: 'Indigo' }, hex: '#4f46e5' },
];

function normalizeColor(value) {
    if (!value) return '';
    return String(value).toLowerCase();
}

function colorOptions(field) {
    return Array.isArray(field?.selection_values) && field.selection_values.length > 0
        ? field.selection_values
        : DEFAULT_COLORS;
}

function colorOption(options, value) {
    const normalized = normalizeColor(value);
    return options.find((color) => normalizeColor(color.value) === normalized)
        ?? null;
}

function colorLabel(color, lang) {
    return localizedValue(color?.label ?? color?.name, lang) || color?.value || '';
}

function ColorSwatch({ color, selected = false }) {
    return (
        <span
            class={`inline-block size-5 shrink-0 rounded-full border ${selected ? 'border-[var(--dash-text)] ring-2 ring-[var(--dash-accent)] ring-offset-2 ring-offset-[var(--dash-surface)]' : 'border-[var(--dash-border)]'}`}
            style={{ backgroundColor: color?.hex ?? 'transparent' }}
            aria-hidden="true"
        />
    );
}

export function ColorField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const options = colorOptions(field);
    const selected = colorOption(options, value);
    if (isFieldReadOnly(field, readOnly)) {
        if (!selected) return <span class="text-[var(--dash-text-soft)]">—</span>;
        return (
            <span class="inline-flex items-center gap-2 text-[var(--dash-text)]">
                <ColorSwatch color={selected} />
                <span>{colorLabel(selected, lang)}</span>
            </span>
        );
    }

    return (
        <div class="flex flex-wrap gap-2" role="radiogroup" aria-label={fieldLabel(field, lang)}>
            {options.map((color) => {
                const checked = normalizeColor(selected?.value) === normalizeColor(color.value);
                const label = colorLabel(color, lang);
                return (
                    <button
                        type="button"
                        key={color.value}
                        class="grid size-8 place-items-center rounded-md border border-[var(--dash-border)] bg-[var(--dash-surface)] transition hover:border-[var(--dash-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--dash-accent)]"
                        role="radio"
                        aria-checked={String(checked)}
                        aria-label={label}
                        data-tooltip={label}
                        onClick={() => onChange(field.name, color.value)}
                    >
                        <ColorSwatch color={color} selected={checked} />
                    </button>
                );
            })}
        </div>
    );
}
