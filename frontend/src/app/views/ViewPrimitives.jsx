import { useEffect, useState } from 'preact/hooks';

import { FieldControl, FormField } from '../components/fields/index.js';
import { icon, faFloppyDisk, faPaperPlane, faPlus, faXmark } from '../components/icon.js';
import { createEmptyRecord, getFormLayout } from './formLayout.js';
import { fieldLabel } from '../components/fields/fieldHelpers.js';
import { createSystemModelRecord } from '../api/systemModel.js';
import { dashboardActions } from '../store/actions/index.js';
import { authSignal } from '../store/authStore.js';

const EMPTY_INITIAL_VALUES = {};

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

export function SchemaFormLayout({ schema, record, setValue, lang, context, readOnly, errors = {} }) {
    const layout = getFormLayout(schema);
    const [activeTab, setActiveTab] = useState(layout.tabs[0]?.position ?? null);
    useEffect(() => setActiveTab(layout.tabs[0]?.position ?? null), [schema]);
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
                                context={context} error={errors[field.name]} hideLabel />)}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}

export function CreateModal({ data = {}, lang = 'en', open, onClose, initialValues = EMPTY_INITIAL_VALUES }) {
    const schema = data?.model?.schema ?? [];
    const isMessage = data?.model?.name === 'system.message';
    const context = { ...(data?.model ?? {}), tags: data?.model?.tags ?? [] };
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
    useEffect(() => { if (open) { setRecord(initialRecord()); setErrors({}); setSaveError(''); setSaving(false); setDirtyFields(new Set(Object.keys(initialValues))); } }, [open, schema, initialValues]);
    useEffect(() => {
        if (!open) return undefined;
        const close = (event) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', close);
        return () => document.removeEventListener('keydown', close);
    }, [open, onClose]);
    if (!open) return null;
    const layout = getFormLayout(schema);
    const title = `${lang === 'es' ? 'Crear' : 'Create'} ${data?.model?.label?.[lang] ?? data?.model?.name ?? ''}`;
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
            const values = Object.fromEntries(Object.entries(record).filter(([name, value]) => (
                dirtyFields.has(name) && hasValue(value)
            )));
            const created = await createSystemModelRecord({ model: data?.model?.name, values });
            dashboardActions.addModelRecord(created);
            onClose();
        } catch (error) {
            console.error('Unable to create model record.', error);
            setSaveError(lang === 'es' ? 'No se pudo crear el registro. Revisa los datos e inténtalo de nuevo.' : 'Unable to create the record. Check the data and try again.');
        } finally {
            setSaving(false);
        }
    };
    const headerControl = (field) => field && (
        <div class="form-field" data-form-field={field.name}>
            <label class="form-field-label">{fieldLabel(field, lang)}
                {(field?.form?.required === true || field?.required === true) && <span class="form-required-mark" aria-hidden="true"> *</span>}
            </label>
            <FieldControl field={field} value={record[field.name]} onChange={setValue} lang={lang} context={context} />
            {errors[field.name] && <span role="alert" data-field-error={field.name} class="mt-1 block text-xs text-[var(--dash-danger)]">{errors[field.name]}</span>}
        </div>
    );
    return (
        <div class="form-modal" data-form-modal>
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
                    <SchemaFormLayout schema={schema} record={record} setValue={setValue} lang={lang}
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
    );
}
