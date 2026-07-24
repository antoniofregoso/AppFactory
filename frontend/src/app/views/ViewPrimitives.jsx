import { useEffect, useState } from 'preact/hooks';

import { FieldControl, FieldHelp, FormField } from '../components/fields/index.js';
import { icon, faFloppyDisk, faPaperPlane, faPlus, faXmark } from '../components/icon.js';
import { createEmptyRecord, getFormLayout } from './formLayout.js';
import { fieldLabel, localizedConfig } from '../components/fields/fieldHelpers.js';
import { createSystemModelRecord, fetchSystemModelView } from '../api/systemModel.js';
import { dashboardActions } from '../store/actions/index.js';
import { authSignal } from '../store/authStore.js';
import { localeKey, localizedValue } from '../utils/ux.js';

const EMPTY_INITIAL_VALUES = {};

export function createRecordErrorMessage(error, lang = 'en') {
    const detail = error?.response?.errors?.[0]?.message;
    const fallback = lang === 'es'
        ? 'No se pudo crear el registro. Revisa los datos e inténtalo de nuevo.'
        : 'Unable to create the record. Check the data and try again.';
    if (!detail) return fallback;
    return lang === 'es'
        ? `No se pudo crear el registro: ${detail}`
        : `Unable to create the record: ${detail}`;
}

export function useMany2oneCreate(lang = 'en') {
    const [relationModal, setRelationModal] = useState(null);
    const open = async ({ field, query = '', onCreated }) => {
        const model = field?.model;
        if (!model) return;
        try {
            const data = await fetchSystemModelView({ model });
            if (data?.model?.readonly === true) throw new Error(`Model ${model} is read-only`);
            const schema = data?.model?.schema ?? [];
            const titleField = schema.find((item) => String(item?.form?.header ?? '').toLowerCase() === 'title')
                ?? schema.find((item) => item.name === 'name');
            let initialValues = EMPTY_INITIAL_VALUES;
            if (query && titleField) {
                const initialValue = ['string_i18n', 'html'].includes(titleField.type)
                    ? { [localeKey(lang)]: query }
                    : query;
                initialValues = { [titleField.name]: initialValue };
            }
            setRelationModal({ data, model, initialValues, onCreated });
        } catch (error) {
            console.error('Unable to load the related record form.', error);
            window.alert(lang === 'es' ? 'No se pudo abrir el formulario del elemento.' : 'Unable to open the item form.');
        }
    };
    const modal = relationModal && (
        <CreateModal data={relationModal.data} lang={lang} open initialValues={relationModal.initialValues}
            onClose={() => setRelationModal(null)}
            onCreated={(created) => {
                relationModal.onCreated?.({ ...created, model: relationModal.model });
                setRelationModal(null);
            }} />
    );
    return { open, modal };
}

export function Icon({ definition, class: className = '' }) {
    return <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(definition, className) }} />;
}

export function ViewHeader({ title = '', count = null, lang = 'en', class: className = '', actions = null, onCreate }) {
    const label = lang === 'es' ? 'Crear' : 'Create';
    return (
        <header class={`mb-5 flex items-center justify-between gap-4 ${className}`.trim()}>
            <div class="flex items-baseline gap-3">
                <h2 class="text-base font-semibold text-[var(--dash-text)]">{title}</h2>
                {count != null && <span class="text-xs text-[var(--dash-text-muted)]">{count}</span>}
            </div>
            <div class="flex items-center gap-2">
                {actions}
                {onCreate && <button type="button" class="topbar-action-btn" aria-label={label} data-tooltip={label}
                    data-create-open onClick={onCreate}>
                    <Icon definition={faPlus} class="topbar-action-icon" />
                </button>}
            </div>
        </header>
    );
}

function FormColumns({ layout, record, setValue, lang, context, readOnly, errors = {} }) {
    const renderField = ({ field }) => (
        <FormField key={field.name} field={field} value={record[field.name]} onChange={setValue}
            lang={lang} readOnly={readOnly} context={context} error={errors[field.name]} />
    );
    return (
        <>
            {(layout.leftColumn.length > 0 || layout.rightColumn.length > 0) && (
                <div class="form-record-body grid gap-x-8 gap-y-4 px-5 py-5 md:grid-cols-2">
                    <div class="flex min-w-0 flex-col gap-4">{layout.leftColumn.map(renderField)}</div>
                    <div class="flex min-w-0 flex-col gap-4">{layout.rightColumn.map(renderField)}</div>
                </div>
            )}
        </>
    );
}

function relatedModelName(field, items) {
    if (field?.model) return field.model;
    return (Array.isArray(items) ? items : []).find((item) => item?.model)?.model ?? '';
}

function parentReference(context, lang) {
    const record = context?.record ?? {};
    return {
        uuid: record.uuid,
        model: context?.name,
        name: localizedValue(record.name, lang) || record.code || record.email || record.uuid,
    };
}

function inverseRelation(schema, parentModel, relationName = '') {
    if (relationName) return schema.find((field) => field?.name === relationName) ?? null;
    const candidates = schema.filter((field) => (
        ['many2one', 'many2one_avatar'].includes(field?.type) && field?.model === parentModel
    ));
    return candidates.length === 1 ? candidates[0] : null;
}

export function SchemaFormLayout({ schema, record, setValue, onChildCreated, lang, context, readOnly, errors = {} }) {
    const layout = getFormLayout(schema);
    const [activeTab, setActiveTab] = useState(layout.tabs[0]?.position ?? null);
    const [childModal, setChildModal] = useState(null);
    const [creatingChild, setCreatingChild] = useState('');
    const [childCreateError, setChildCreateError] = useState('');
    useEffect(() => setActiveTab(layout.tabs[0]?.position ?? null), [schema]);
    const openChildCreate = onChildCreated ? async (field, items) => {
        const model = relatedModelName(field, items);
        if (!model) return;
        setCreatingChild(field.name);
        setChildCreateError('');
        try {
            const childData = await fetchSystemModelView({ model });
            const relationName = field?.form?.inverse_field ?? field?.inverse_field ?? '';
            const relation = inverseRelation(childData?.model?.schema ?? [], context?.name, relationName);
            if (!relation) throw new Error(`No unambiguous inverse relation from ${model} to ${context?.name}`);
            const deferred = !context?.record?.uuid;
            const initialValues = { [relation.name]: parentReference(context, lang) };
            setChildModal({ field, model, data: childData, relation, initialValues, deferred });
        } catch (error) {
            console.error('Unable to load the child record form.', error);
            setChildCreateError(lang === 'es' ? 'No se pudo abrir el formulario del elemento hijo.' : 'Unable to open the child record form.');
        } finally {
            setCreatingChild('');
        }
    } : null;
    return (
        <>
            <FormColumns layout={layout} record={record} setValue={setValue} lang={lang} context={context} readOnly={readOnly} errors={errors} />
            {layout.tabs.length > 0 && (
                <div class="form-record-tabs" data-record-tabs>
                    <div class="form-record-tab-list" role="tablist">
                        {layout.tabs.map((tab) => {
                            const field = tab.fields[0]?.field;
                            const active = activeTab === tab.position;
                            return <button type="button" role="tab" class={`form-record-tab ${active ? 'form-record-tab--active' : ''}`}
                                aria-selected={String(active)} data-record-tab={tab.position} key={tab.position}
                                onClick={() => setActiveTab(tab.position)}>{field?.label?.[lang] ?? field?.name}</button>;
                        })}
                    </div>
                    {layout.tabs.map((tab) => (
                        <div role="tabpanel" class="form-record-tab-panel" hidden={activeTab !== tab.position}
                            data-record-tab-panel={tab.position} key={tab.position}>
                            {tab.fields.map(({ field }) => <FormField key={field.name} field={field}
                                value={record[field.name]} onChange={setValue} lang={lang} readOnly={readOnly}
                                context={context} error={errors[field.name]} hideLabel
                                childCreating={creatingChild === field.name}
                                onCreateChild={openChildCreate && relatedModelName(field, record[field.name]) ? openChildCreate : null} />)}
                            {childCreateError && <p role="alert" class="mt-3 text-sm text-[var(--dash-danger)]">{childCreateError}</p>}
                        </div>
                    ))}
                </div>
            )}
            {childModal && (
                <CreateModal data={childModal.data} lang={lang} open initialValues={childModal.initialValues}
                    deferCreate={childModal.deferred}
                    onClose={() => setChildModal(null)}
                    onCreated={(created) => {
                        const { __draftValues, ...recordValues } = created;
                        onChildCreated(childModal.field, {
                            ...recordValues,
                            model: childModal.model,
                            ...(childModal.deferred ? {
                                __draft: {
                                    model: childModal.model,
                                    inverseField: childModal.relation.name,
                                    values: __draftValues,
                                },
                            } : {}),
                        });
                        setChildModal(null);
                    }} />
            )}
        </>
    );
}

export function CreateModal({ data = {}, lang = 'en', open, onClose, onCreated, initialValues = EMPTY_INITIAL_VALUES, deferCreate = false, copyMode = false }) {
    const schema = data?.model?.schema ?? [];
    const isMessage = data?.model?.name === 'system.message';
    const many2oneCreate = useMany2oneCreate(lang);
    const initialRecord = () => ({
        ...createEmptyRecord(schema),
        ...(data?.model?.name === 'system.message' ? {
            status: 'Sent',
            from_user_id: {
                uuid: authSignal.value.uuid,
                name: authSignal.value.name,
                email: authSignal.value.email,
                model: 'user.user',
            },
        } : {}),
        ...initialValues,
    });
    const [record, setRecord] = useState(initialRecord);
    const [errors, setErrors] = useState({});
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState('');
    const [dirtyFields, setDirtyFields] = useState(() => new Set());
    const context = {
        ...(data?.model ?? {}),
        tags: data?.model?.tags ?? [],
        createMany2one: many2oneCreate.open,
        record,
    };
    useEffect(() => { if (open) { setRecord(initialRecord()); setErrors({}); setSaveError(''); setSaving(false); setDirtyFields(new Set(Object.keys(initialValues))); } }, [open, schema, initialValues]);
    useEffect(() => {
        if (!open) return undefined;
        const close = (event) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', close);
        return () => document.removeEventListener('keydown', close);
    }, [open, onClose]);
    if (!open) return null;
    const layout = getFormLayout(schema);
    const title = `${copyMode ? (lang === 'es' ? 'Copiar' : 'Copy') : (lang === 'es' ? 'Crear' : 'Create')} ${data?.model?.label?.[lang] ?? data?.model?.name ?? ''}`;
    const closeLabel = lang === 'es' ? 'Cerrar' : 'Close';
    const saveLabel = isMessage ? (lang === 'es' ? 'Enviar' : 'Send') : (lang === 'es' ? 'Guardar' : 'Save');
    const requiredFields = schema.filter((field) => field?.form?.required === true || field?.required === true);
    const requiredText = lang === 'es' ? 'Campos obligatorios' : 'Required fields';
    const requiredError = lang === 'es' ? 'Este campo es obligatorio.' : 'This field is required.';
    const hasValue = (value) => {
        if (value == null) return false;
        if (typeof value === 'string') return value.trim().length > 0;
        if (Array.isArray(value)) return value.length > 0;
        if (typeof value === 'object') return Object.values(value).some(hasValue);
        return true;
    };
    const setValue = (name, value) => {
        setRecord((current) => ({ ...current, [name]: value }));
        setDirtyFields((current) => new Set(current).add(name));
        setErrors((current) => current[name] ? { ...current, [name]: undefined } : current);
    };
    const save = async () => {
        const nextErrors = Object.fromEntries(requiredFields
            .filter((field) => !hasValue(record[field.name]))
            .map((field) => [field.name, requiredError]));
        setErrors(nextErrors);
        if (Object.keys(nextErrors).length) {
            globalThis.requestAnimationFrame?.(() => document.querySelector('[data-field-error]')?.scrollIntoView?.({ block: 'center' }));
            return;
        }
        setSaving(true);
        setSaveError('');
        try {
            const one2manyNames = new Set(
                schema.filter((field) => field.type?.startsWith('one2many')).map((field) => field.name),
            );
            const values = Object.fromEntries(Object.entries(record).filter(([name, value]) => (
                dirtyFields.has(name) && hasValue(value) && !one2manyNames.has(name)
            )));
            const created = deferCreate
                ? {
                    ...values,
                    uuid: `draft-${globalThis.crypto?.randomUUID?.() ?? Date.now()}`,
                    __draftValues: values,
                }
                : await createSystemModelRecord({ model: data?.model?.name, values });
            if (!deferCreate) {
                for (const field of schema.filter((item) => item.type?.startsWith('one2many'))) {
                    const children = Array.isArray(record[field.name]) ? record[field.name] : [];
                    const persisted = [];
                    for (const child of children) {
                        if (!child.__draft) continue;
                        persisted.push(await createSystemModelRecord({
                            model: child.__draft.model,
                            values: {
                                ...child.__draft.values,
                                [child.__draft.inverseField]: {
                                    uuid: created.uuid,
                                    model: data?.model?.name,
                                    name: localizedValue(created.name, lang) || created.code || created.uuid,
                                },
                            },
                        }));
                    }
                    if (persisted.length) created[field.name] = persisted;
                }
            }
            if (onCreated) onCreated(created);
            else dashboardActions.addModelRecord(created);
            onClose();
        } catch (error) {
            console.error('Unable to create model record.', error);
            setSaveError(createRecordErrorMessage(error, lang));
        } finally {
            setSaving(false);
        }
    };
    const headerControl = (field) => field && (
        <div class="form-field" data-form-field={field.name}>
            <div class="form-field-label-row">
                <label class="form-field-label">{fieldLabel(field, lang)}
                    {(field?.form?.required === true || field?.required === true) && <span class="form-required-mark" aria-hidden="true"> *</span>}
                </label>
                <FieldHelp help={localizedConfig(field, 'help', lang)} lang={lang} />
            </div>
            <FieldControl field={field} value={record[field.name]} onChange={setValue} lang={lang} context={context} />
            {errors[field.name] && <span role="alert" data-field-error={field.name} class="mt-1 block text-xs text-[var(--dash-danger)]">{errors[field.name]}</span>}
        </div>
    );
    return (<>
        <div class="form-modal" data-form-modal data-copy-modal={copyMode ? '' : undefined}>
            <div class="form-modal-backdrop" onClick={onClose} />
            <section class="form-modal-panel" role="dialog" aria-modal="true" aria-label={title}>
                <header class="form-modal-header">
                    <h3 class="text-base font-semibold text-[var(--dash-text)]">{title}</h3>
                    <button type="button" class="topbar-action-btn" aria-label={closeLabel} onClick={onClose}>
                        <Icon definition={faXmark} class="topbar-action-icon" />
                    </button>
                </header>
                <div class="form-modal-body" data-form-mode="edit">
                    {requiredFields.length > 0 && <div class="border-b border-[var(--dash-border)] bg-[var(--dash-accent-soft)] px-5 py-3 text-sm text-[var(--dash-text)]" data-required-fields>
                        <span class="font-semibold">{requiredText}:</span>{' '}
                        {requiredFields.map((field) => fieldLabel(field, lang)).join(', ')}
                    </div>}
                    <div class="flex gap-4 border-b border-[var(--dash-border)] px-5 py-4">
                        {layout.header.image && <div data-form-header="image"><FieldControl field={layout.header.image}
                            value={record[layout.header.image.name]} onChange={setValue} lang={lang} context={context} /></div>}
                        <div class="min-w-0 flex-1">
                            {headerControl(layout.header.title)}
                            {layout.header.subtitle && <div class="mt-3">{headerControl(layout.header.subtitle)}</div>}
                        </div>
                    </div>
                    <SchemaFormLayout schema={schema} record={record} setValue={setValue}
                        onChildCreated={(field, child) => setValue(field.name, [
                            ...(Array.isArray(record[field.name]) ? record[field.name] : []),
                            child,
                        ])} lang={lang}
                        context={context} readOnly={false} errors={errors} />
                </div>
                <footer class="form-modal-footer">
                    {saveError && <span role="alert" data-create-error class="mr-auto text-sm text-[var(--dash-danger)]">{saveError}</span>}
                    <button type="button" class="topbar-action-btn topbar-action-btn--active" aria-label={saveLabel}
                        disabled={saving} onClick={() => { void save(); }}>
                        <Icon definition={isMessage ? faPaperPlane : faFloppyDisk} class="topbar-action-icon" />
                    </button>
                </footer>
            </section>
        </div>
        {many2oneCreate.modal}
    </>);
}
