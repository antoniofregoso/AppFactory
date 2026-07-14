import { COLOR_CLASS, COLOR_FALLBACK } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly } from './fieldHelpers.js';

function getOptions(field, context) {
    return field.selection_values ?? context?.[field.name] ?? context?.status ?? [];
}

function optionLabel(option, value, lang) {
    return option?.[lang] ?? option?.en ?? option?.es ?? value;
}

function SelectionPill({ option, value, lang }) {
    if (value == null || value === '') {
        return <span class="text-[var(--dash-text-soft)]">—</span>;
    }
    return (
        <span class={`inline-flex max-w-full items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${COLOR_CLASS[option?.color] ?? COLOR_FALLBACK}`}>
            <span class="truncate">{optionLabel(option, value, lang)}</span>
        </span>
    );
}

export function SelectionField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const options = getOptions(field, context);
    const option = options.find((item) => item.value === value);
    if (isFieldReadOnly(field, readOnly)) {
        return <SelectionPill option={option} value={value} lang={lang} />;
    }
    return (
        <select name={field.name} class="form-control form-control--edit" value={value ?? ''}
            aria-label={fieldLabel(field, lang)} required={field?.form?.required === true}
            onChange={(event) => onChange(field.name, event.currentTarget.value)}>
            <option value="" />
            {options.map((item) => <option value={item.value} key={item.value}>{optionLabel(item, item.value, lang)}</option>)}
        </select>
    );
}
