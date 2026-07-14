import { useState } from 'preact/hooks';

import { icon, faXmark } from '../icon.js';
import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { fieldLabel, isFieldReadOnly } from './fieldHelpers.js';

function itemName(item) {
    return typeof item === 'object' && item !== null ? (item.name ?? '') : String(item ?? '');
}

function itemKey(item, index) {
    return typeof item === 'object' && item !== null ? String(item.uuid ?? item.name ?? index) : `${item}-${index}`;
}

function itemHref(item) {
    return typeof item === 'object' && item?.model && item?.uuid != null ? buildRecordUrl(item.model, item.uuid) : '';
}

/**
 * Shared list-of-related-records control used by both `one2many` and `many2many`.
 * There is no relation search/autocomplete backend yet, so editing is limited to
 * removing existing links and (when `allowAdd`) appending a plain-name placeholder.
 */
export function RelationList({ field, value, onChange, lang = 'en', readOnly = false, allowAdd = true }) {
    const items = Array.isArray(value) ? value : [];
    const [draft, setDraft] = useState('');

    if (isFieldReadOnly(field, readOnly)) {
        if (items.length === 0) return <span class="text-[var(--dash-text-soft)]">—</span>;
        return (
            <ul class="flex flex-col gap-1">
                {items.map((item, index) => {
                    const href = itemHref(item);
                    const name = itemName(item) || '—';
                    return (
                        <li key={itemKey(item, index)}>
                            {href
                                ? <a href={href} onClick={() => rememberRecordBreadcrumb(href, name)}
                                    class="font-medium text-[var(--dash-accent)] hover:underline">{name}</a>
                                : <span class="text-[var(--dash-text)]">{name}</span>}
                        </li>
                    );
                })}
            </ul>
        );
    }

    const remove = (index) => onChange(field.name, items.filter((_, itemIndex) => itemIndex !== index));
    const add = (rawName) => {
        const name = rawName.trim();
        if (!name) return;
        onChange(field.name, [...items, { name }]);
        setDraft('');
    };

    return (
        <div class="flex flex-col gap-2">
            <div class="flex flex-wrap gap-1">
                {items.map((item, index) => (
                    <span key={itemKey(item, index)} class="form-tag-chip bg-zinc-100 text-zinc-700">
                        <span>{itemName(item) || '—'}</span>
                        <button type="button" class="form-tag-chip-remove"
                            aria-label={`${lang === 'es' ? 'Quitar' : 'Remove'} ${itemName(item)}`}
                            onClick={() => remove(index)}
                            dangerouslySetInnerHTML={{ __html: icon(faXmark, 'form-tag-chip-remove-icon') }} />
                    </span>
                ))}
            </div>
            {allowAdd && (
                <div class="flex gap-2">
                    <input type="text" class="form-control form-control--edit" value={draft}
                        aria-label={fieldLabel(field, lang)}
                        placeholder={lang === 'es' ? 'Agregar por nombre…' : 'Add by name…'}
                        onInput={(event) => setDraft(event.currentTarget.value)}
                        onKeyDown={(event) => {
                            if (event.key !== 'Enter') return;
                            event.preventDefault();
                            add(event.currentTarget.value);
                        }} />
                    <button type="button" class="topbar-action-btn" onClick={() => add(draft)} aria-label={lang === 'es' ? 'Agregar' : 'Add'}>
                        {lang === 'es' ? 'Agregar' : 'Add'}
                    </button>
                </div>
            )}
        </div>
    );
}
