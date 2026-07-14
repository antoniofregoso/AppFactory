import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { icon, faMagnifyingGlass, faXmark } from '../icon.js';
import { COLOR_CLASS, COLOR_FALLBACK, localizedValue, resolveTags } from '../../utils/ux.js';
import { isFieldReadOnly } from './fieldHelpers.js';

function tagIdentity(tag) {
    return String(tag?.uuid ?? tag?.value ?? localizedValue(tag?.name, 'en'));
}

function mergeTagOptions(availableTags, selectedTags) {
    const tags = new Map();
    [...(availableTags ?? []), ...(selectedTags ?? [])].forEach((tag) => {
        if (tag && typeof tag === 'object') tags.set(tagIdentity(tag), tag);
    });
    return Array.from(tags.values());
}

function Pill({ tag, lang }) {
    const classes = COLOR_CLASS[tag.color] ?? COLOR_FALLBACK;
    return <span class={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${classes}`}>{localizedValue(tag.name, lang)}</span>;
}

function TagChip({ tag, lang, onRemove }) {
    const classes = COLOR_CLASS[tag.color] ?? COLOR_FALLBACK;
    const name = localizedValue(tag.name, lang);
    return (
        <button type="button" class={`form-tag-chip ${classes}`}
            aria-label={`${lang === 'es' ? 'Quitar' : 'Remove'} ${name}`}
            onClick={(event) => { event.stopPropagation(); onRemove(tagIdentity(tag)); }}>
            <span>{name}</span>
            <span class="form-tag-chip-remove" aria-hidden="true"
                dangerouslySetInnerHTML={{ __html: icon(faXmark, 'form-tag-chip-remove-icon') }} />
        </button>
    );
}

export function Many2manyPillsField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const catalog = field?.options ?? context.tags ?? [];
    const selectedTags = useMemo(() => resolveTags(value, catalog), [value, catalog]);
    const availableTags = useMemo(() => mergeTagOptions(catalog, selectedTags), [catalog, selectedTags]);

    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [activeIndex, setActiveIndex] = useState(-1);
    const rootRef = useRef(null);
    const searchRef = useRef(null);

    useEffect(() => setActiveIndex(0), [query]);

    useEffect(() => {
        if (!open) return undefined;
        const onPointerDown = (event) => {
            if (!rootRef.current?.contains(event.target)) setOpen(false);
        };
        document.addEventListener('pointerdown', onPointerDown);
        return () => document.removeEventListener('pointerdown', onPointerDown);
    }, [open]);

    if (isFieldReadOnly(field, readOnly)) {
        if (selectedTags.length === 0) return <span class="text-[var(--dash-text-soft)]">—</span>;
        return <div class="flex flex-wrap gap-1">{selectedTags.map((tag) => <Pill tag={tag} lang={lang} key={tagIdentity(tag)} />)}</div>;
    }

    const visibleOptions = availableTags.filter((tag) => (
        localizedValue(tag.name, lang).toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())
    ));
    const selectedIds = new Set(selectedTags.map(tagIdentity));

    const toggle = (id) => {
        const tag = availableTags.find((item) => tagIdentity(item) === id);
        if (!tag) return;
        const next = selectedIds.has(id)
            ? selectedTags.filter((item) => tagIdentity(item) !== id)
            : [...selectedTags, tag];
        onChange(field.name, next.map(tagIdentity));
        setQuery('');
        searchRef.current?.focus();
    };

    const openMenu = () => setOpen(true);

    const onSearchKeyDown = (event) => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            if (!open) {
                openMenu();
                return;
            }
            setActiveIndex((current) => {
                const count = visibleOptions.length;
                if (count === 0) return -1;
                return (current + (event.key === 'ArrowDown' ? 1 : -1) + count) % count;
            });
        } else if (event.key === 'Enter' && open && visibleOptions[activeIndex]) {
            event.preventDefault();
            toggle(tagIdentity(visibleOptions[activeIndex]));
        } else if (event.key === 'Escape') {
            event.preventDefault();
            setOpen(false);
        } else if (event.key === 'Backspace' && query === '' && selectedTags.length > 0) {
            toggle(tagIdentity(selectedTags[selectedTags.length - 1]));
        } else if (event.key === 'Tab') {
            setOpen(false);
        }
    };

    const isUserRelation = field?.model === 'user.user' || field?.name === 'to_users';
    const searchLabel = isUserRelation
        ? (lang === 'es' ? 'Buscar usuarios…' : 'Search users…')
        : (lang === 'es' ? 'Buscar etiquetas…' : 'Search tags…');
    const emptyLabel = isUserRelation
        ? (lang === 'es' ? 'No hay usuarios que coincidan' : 'No matching users')
        : (lang === 'es' ? 'No hay etiquetas que coincidan' : 'No matching tags');
    const availableLabel = isUserRelation
        ? (lang === 'es' ? 'Usuarios disponibles' : 'Available users')
        : (lang === 'es' ? 'Etiquetas disponibles' : 'Available tags');
    const countLabel = lang === 'es'
        ? `${selectedTags.length} de ${availableTags.length} seleccionadas`
        : `${selectedTags.length} of ${availableTags.length} selected`;

    return (
        <div class={`form-tag-picker ${open ? 'form-tag-picker--open' : ''}`} data-tag-picker ref={rootRef}>
            <div class="form-tag-picker-control" onClick={() => { openMenu(); searchRef.current?.focus(); }}>
                <div class="form-tag-picker-selections">
                    {selectedTags.map((tag) => <TagChip tag={tag} lang={lang} onRemove={toggle} key={tagIdentity(tag)} />)}
                </div>
                <div class="form-tag-picker-search-row">
                    <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faMagnifyingGlass, 'form-tag-picker-search-icon') }} />
                    <input ref={searchRef} type="search" class="form-tag-picker-search" autocomplete="off"
                        aria-label={searchLabel} aria-expanded={String(open)} aria-haspopup="listbox"
                        placeholder={searchLabel} value={query}
                        onInput={(event) => { setQuery(event.currentTarget.value); openMenu(); }}
                        onFocus={openMenu} onKeyDown={onSearchKeyDown} />
                </div>
            </div>
            {open && (
                <div class="form-tag-picker-menu" data-tag-picker-menu>
                    <div class="form-tag-picker-menu-header">
                        <span>{availableLabel}</span>
                        <span>{countLabel}</span>
                    </div>
                    <div class="form-tag-picker-options" role="listbox" aria-multiselectable="true" aria-label={availableLabel}>
                        {visibleOptions.map((tag, index) => {
                            const id = tagIdentity(tag);
                            return (
                                <button type="button" key={id}
                                    class={`form-tag-picker-option ${index === activeIndex ? 'form-tag-picker-option--active' : ''}`}
                                    role="option" aria-selected={String(selectedIds.has(id))} onClick={() => toggle(id)}>
                                    <span class={`form-tag-color form-tag-color--${tag.color ?? 'zinc'}`} />
                                    <span class="form-tag-picker-option-name">{localizedValue(tag.name, lang)}</span>
                                    <span class="form-tag-picker-option-check" aria-hidden="true" />
                                </button>
                            );
                        })}
                        {visibleOptions.length === 0 && <p class="form-tag-picker-empty">{emptyLabel}</p>}
                    </div>
                </div>
            )}
            <span class="sr-only" aria-live="polite">{countLabel}</span>
        </div>
    );
}
