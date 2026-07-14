import { useEffect, useMemo, useState } from 'preact/hooks';

import { fetchSystemModelView } from '../../api/systemModel.js';
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

export function Many2oneField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const model = field?.model;
    const { loading, options } = useRelatedOptions(isFieldReadOnly(field, readOnly) ? null : model);
    const name = getRecordLabel(value, lang) || value || '';
    const selectedUuid = value?.uuid ? String(value.uuid) : '';
    const placeholder = plainText(localizedConfig(field, 'placeholder', lang));
    const required = field?.form?.required === true || field?.required === true;
    const selectOptions = useMemo(() => options
        .slice()
        .sort((left, right) => getRecordLabel(left, lang).localeCompare(getRecordLabel(right, lang))),
    [options, lang]);

    if (isFieldReadOnly(field, readOnly)) {
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

    if (model) {
        return (
            <select name={field.name} class="form-control form-control--edit" value={selectedUuid}
                aria-label={fieldLabel(field, lang)} required={required} disabled={loading}
                onChange={(event) => {
                    const next = selectOptions.find((item) => String(item.uuid) === event.currentTarget.value);
                    onChange(field.name, next ?? null);
                }}>
                <option value="">{loading ? (lang === 'es' ? 'Cargando...' : 'Loading...') : placeholder}</option>
                {selectOptions.map((item) => (
                    <option value={String(item.uuid)} key={item.uuid}>
                        {getRecordLabel(item, lang)}
                    </option>
                ))}
            </select>
        );
    }

    return (
        <input type="text" name={field.name} class="form-control form-control--edit" value={name}
            aria-label={fieldLabel(field, lang)} placeholder={placeholder}
            onInput={(event) => onChange(field.name, { ...(typeof value === 'object' && value !== null ? value : {}), name: event.currentTarget.value })} />
    );
}
