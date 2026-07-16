import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { fetchSystemModelView } from '../../api/systemModel.js';
import { faMagnifyingGlass, faPlus, faXmark, icon } from '../icon.js';
import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { localizedValue } from '../../utils/ux.js';
import { fieldLabel, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';

const relatedOptionsCache = new Map();

function isActiveOption(record, model) {
    if (model === 'system.currency') return true;
    return !Object.hasOwn(record, 'active') || record.active === true;
}

function getRecordLabel(record, lang) {
    return localizedValue(record?.display_name, lang)
        || localizedValue(record?.name, lang)
        || localizedValue(record?.label, lang)
        || localizedValue(record?.title, lang)
        || record?.code
        || record?.email
        || record?.uuid
        || '';
}

function normalizeOption(record, model) {
    return { ...record, model };
}

function useRelatedOptions(model) {
    const [state, setState] = useState(() => ({
        loading: Boolean(model),
        options: relatedOptionsCache.get(model) ?? [],
    }));

    useEffect(() => {
        if (!model) {
            setState({ loading: false, options: [] });
            return undefined;
        }

        const cached = relatedOptionsCache.get(model);
        if (cached) {
            setState({ loading: false, options: cached });
            return undefined;
        }

        let cancelled = false;
        setState((current) => ({ ...current, loading: true }));
        fetchSystemModelView({ model })
            .then((view) => {
                if (cancelled) return;
                const options = (view?.records ?? [])
                    .filter((record) => isActiveOption(record, model))
                    .map((record) => normalizeOption(record, model));
                relatedOptionsCache.set(model, options);
                setState({ loading: false, options });
            })
            .catch(() => {
                if (!cancelled) setState({ loading: false, options: [] });
            });

        return () => { cancelled = true; };
    }, [model]);

    return state;
}

function mergeSelectedOption(options, value, model) {
    if (!value || typeof value !== 'object' || value.uuid == null) return options;
    if (options.some((option) => String(option.uuid) === String(value.uuid))) return options;
    return [normalizeOption(value, value.model || model), ...options];
}

export function Many2oneField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const model = field?.model;
    const editable = !isFieldReadOnly(field, readOnly);
    const { loading, options } = useRelatedOptions(editable ? model : null);
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [activeIndex, setActiveIndex] = useState(0);
    const rootRef = useRef(null);
    const inputRef = useRef(null);
    const name = getRecordLabel(value, lang) || value || '';
    const selectedUuid = value?.uuid ? String(value.uuid) : '';
    const placeholder = plainText(localizedConfig(field, 'placeholder', lang));
    const required = field?.form?.required === true || field?.required === true;
    const createRelated = context?.createMany2one;
    const selectOptions = useMemo(() => mergeSelectedOption(options, value, model)
        .slice()
        .sort((left, right) => getRecordLabel(left, lang).localeCompare(getRecordLabel(right, lang))),
    [options, value, model, lang]);
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const visibleOptions = selectOptions.filter((option) => (
        `${getRecordLabel(option, lang)} ${option?.code ?? ''} ${option?.email ?? ''}`
            .toLocaleLowerCase()
            .includes(normalizedQuery)
    ));

    useEffect(() => setActiveIndex(0), [query]);
    useEffect(() => {
        if (!open) return undefined;
        const close = (event) => {
            if (!rootRef.current?.contains(event.target)) {
                setOpen(false);
                setQuery('');
            }
        };
        document.addEventListener('pointerdown', close);
        return () => document.removeEventListener('pointerdown', close);
    }, [open]);

    if (!editable) {
        if (!name) return <span class="text-[var(--dash-text-soft)]">—</span>;
        const href = value?.model && value?.uuid != null ? buildRecordUrl(value.model, value.uuid) : '';
        return href
            ? (
                <a href={href} onClick={() => rememberRecordBreadcrumb(href, name)} class="font-medium text-[var(--dash-accent)] hover:underline
                    focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2
                    focus-visible:outline-[var(--dash-accent)]">{name}</a>
            )
            : <span class="text-[var(--dash-text)]">{name}</span>;
    }

    if (!model) {
        return (
            <input type="text" name={field.name} class="form-control form-control--edit" value={name}
                aria-label={fieldLabel(field, lang)} placeholder={placeholder}
                onInput={(event) => onChange(field.name, { ...(typeof value === 'object' && value !== null ? value : {}), name: event.currentTarget.value })} />
        );
    }

    const choose = (option) => {
        onChange(field.name, option);
        setOpen(false);
        setQuery('');
    };
    const onKeyDown = (event) => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            setOpen(true);
            setActiveIndex((current) => {
                if (!visibleOptions.length) return -1;
                return (current + (event.key === 'ArrowDown' ? 1 : -1) + visibleOptions.length) % visibleOptions.length;
            });
        } else if (event.key === 'Enter' && open && visibleOptions[activeIndex]) {
            event.preventDefault();
            choose(visibleOptions[activeIndex]);
        } else if (event.key === 'Escape') {
            setOpen(false);
            setQuery('');
        }
    };
    const addLabel = lang === 'es' ? 'Agregar elemento' : 'Add item';

    return (
        <div class={`form-tag-picker ${open ? 'form-tag-picker--open' : ''}`} ref={rootRef} data-many2one-picker={field.name}>
            <div class="form-tag-picker-control" onClick={() => { setOpen(true); inputRef.current?.focus(); }}>
                <div class="form-tag-picker-search-row">
                    <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faMagnifyingGlass, 'form-tag-picker-search-icon') }} />
                    <input ref={inputRef} type="search" name={field.name} class="form-tag-picker-search"
                        autocomplete="off" required={required} disabled={loading}
                        aria-label={fieldLabel(field, lang)} aria-expanded={String(open)} aria-haspopup="listbox"
                        placeholder={loading ? (lang === 'es' ? 'Cargando…' : 'Loading…') : placeholder}
                        value={open ? query : name}
                        onFocus={() => { setOpen(true); setQuery(''); }}
                        onInput={(event) => { setQuery(event.currentTarget.value); setOpen(true); }}
                        onKeyDown={onKeyDown} />
                    {selectedUuid && !open && <button type="button" class="form-tag-chip-remove" aria-label={lang === 'es' ? 'Quitar selección' : 'Clear selection'}
                        onClick={(event) => { event.stopPropagation(); onChange(field.name, null); }}
                        dangerouslySetInnerHTML={{ __html: icon(faXmark, 'form-tag-chip-remove-icon') }} />}
                </div>
            </div>
            {open && (
                <div class="form-tag-picker-menu" data-many2one-menu>
                    <div class="form-tag-picker-menu-header">
                        <span>{lang === 'es' ? 'Opciones disponibles' : 'Available options'}</span>
                        <span>{visibleOptions.length}</span>
                    </div>
                    <div class="form-tag-picker-options" role="listbox" aria-label={fieldLabel(field, lang)}>
                        {visibleOptions.map((option, index) => (
                            <button type="button" class={`form-tag-picker-option ${index === activeIndex ? 'form-tag-picker-option--active' : ''}`}
                                role="option" aria-selected={String(String(option.uuid) === selectedUuid)}
                                onClick={() => choose(option)} key={option.uuid}>
                                <span class="form-tag-picker-option-name">{getRecordLabel(option, lang)}</span>
                                <span class="form-tag-picker-option-check" aria-hidden="true" />
                            </button>
                        ))}
                        {!loading && visibleOptions.length === 0 && <p class="form-tag-picker-empty">{lang === 'es' ? 'No hay coincidencias' : 'No matches'}</p>}
                        {createRelated && <button type="button" class="form-tag-picker-option" data-many2one-add={field.name}
                            onClick={() => {
                                setOpen(false);
                                void createRelated({
                                    field,
                                    query: query.trim(),
                                    onCreated: (created) => {
                                        const option = normalizeOption(created, created.model || model);
                                        const cached = relatedOptionsCache.get(model) ?? [];
                                        relatedOptionsCache.set(model, [
                                            option,
                                            ...cached.filter((item) => String(item.uuid) !== String(option.uuid)),
                                        ]);
                                        choose(option);
                                    },
                                });
                            }}>
                            <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faPlus, 'form-tag-picker-search-icon') }} />
                            <span class="form-tag-picker-option-name">{query.trim() ? `${addLabel}: ${query.trim()}` : addLabel}</span>
                        </button>}
                    </div>
                </div>
            )}
        </div>
    );
}
