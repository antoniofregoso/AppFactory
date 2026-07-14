import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'preact/hooks';

import { updateSystemModelRecord } from '../api/systemModel.js';
import { CommunicationPanel } from '../components/communicationPanel.jsx';
import { FieldControl } from '../components/fields/index.js';
import { One2manyFollowersField } from '../components/fields/One2manyFollowersField.jsx';
import { faBoxArchive, faChevronLeft, faChevronRight, faFloppyDisk, faPaperPlane, faPen, faTrash } from '../components/icon.js';
import { dashboardActions } from '../store/actions/index.js';
import { buildRecordUrl } from '../utils/index.js';
import { getFormLayout } from './formLayout.js';
import { CreateModal, Icon, SchemaFormLayout, ViewHeader } from './ViewPrimitives.jsx';
import { authSignal } from '../store/authStore.js';
import { refreshPendingCounts } from '../api/pendingCounts.js';
import { localizedValue } from '../utils/ux.js';
import { formatDateTime } from '../utils/formatters.js';

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function replyMessage(record, lang) {
    const original = localizedValue(record.message, lang);
    const sender = record.from_user_id?.name || record.from_user_id?.email || '';
    const subject = localizedValue(record.subject, lang);
    const rawDate = record.date || record.created_at;
    const date = rawDate ? formatDateTime(rawDate, lang === 'es' ? 'es-MX' : 'en-US') : '';
    const labels = lang === 'es'
        ? { heading: 'Mensaje original', from: 'De', date: 'Fecha', subject: 'Asunto' }
        : { heading: 'Original message', from: 'From', date: 'Date', subject: 'Subject' };
    const details = [
        sender && `<strong>${labels.from}:</strong> ${escapeHtml(sender)}`,
        date && `<strong>${labels.date}:</strong> ${escapeHtml(date)}`,
        subject && `<strong>${labels.subject}:</strong> ${escapeHtml(subject)}`,
    ].filter(Boolean).join('<br>');
    return `<p><br></p><p>---------- ${labels.heading} ----------</p><p>${details}</p><blockquote>${original}</blockquote>`;
}

function findRelatedRecord(records, model, uuid) {
    for (const record of records) {
        const related = Object.values(record).find((value) => value && typeof value === 'object' && !Array.isArray(value)
            && value.model === model && String(value.uuid) === String(uuid));
        if (related) return related;
    }
    return null;
}

function getRecord(data, routeUuid, recordModel) {
    const records = data?.records ?? [];
    if (routeUuid == null) return records[0] ?? {};
    if (!recordModel || recordModel === data?.model?.name) return records.find((record) => String(record.uuid) === String(routeUuid)) ?? { uuid: routeUuid };
    return findRelatedRecord(records, recordModel, routeUuid) ?? { uuid: routeUuid, name: `${recordModel} ${routeUuid}`, model: recordModel };
}

function inferSchema(record) {
    return Object.keys(record).filter((name) => name !== 'avatar').map((name, index) => ({
        name, type: 'string', label: { es: name === 'name' ? 'Nombre' : name, en: name === 'name' ? 'Name' : name },
        form: index === 0 ? { header: 'title' } : { leftColumn: index - 1 },
    }));
}

function getNavigableRecords(data, recordModel) {
    if (!recordModel || recordModel === data?.model?.name) return data?.records ?? [];
    const records = new Map();
    for (const record of data?.records ?? []) for (const value of Object.values(record)) {
        if (value && typeof value === 'object' && !Array.isArray(value) && value.model === recordModel && value.uuid != null) records.set(String(value.uuid), value);
    }
    return [...records.values()];
}

function Action({ definition, label, ...props }) {
    return <button type="button" class="topbar-action-btn" aria-label={label} data-tooltip={label} {...props}>
        <Icon definition={definition} class="topbar-action-icon" />
    </button>;
}

function FooterFields({ fields, record, setValue, lang, context, readOnly }) {
    if (!fields?.length) return null;
    return (
        <div class="flex min-w-0 items-center gap-3">
            {fields.map(({ field }) => (
                <FieldControl key={field.name} field={field} value={record[field.name]}
                    onChange={setValue} lang={lang} readOnly={readOnly} context={context} />
            ))}
        </div>
    );
}

function defaultFollowersField(field) {
    return {
        name: 'followers',
        type: 'one2many_followers',
        label: { es_MX: 'Seguidores', es: 'Seguidores', en_US: 'Followers', en: 'Followers' },
        form: { footer: 'left' },
        options: field?.options ?? [],
    };
}

function followersField(schema) {
    const followerField = schema.find((field) => field.type === 'one2many_followers');
    return defaultFollowersField(followerField);
}

function RecordFooter({ data, record, recordModel, lang, followers, right }) {
    const records = getNavigableRecords(data, recordModel);
    const index = records.findIndex((item) => String(item.uuid) === String(record.uuid));
    const model = recordModel || data?.model?.name;
    const targets = [index > 0 ? records[index - 1] : null, index >= 0 && index < records.length - 1 ? records[index + 1] : null];
    const labels = lang === 'es' ? ['Registro anterior', 'Registro siguiente'] : ['Previous record', 'Next record'];
    return <footer class="form-record-footer">
        <div class="min-w-0">{followers}</div>
        <div class="hidden min-w-0 items-center gap-3">{right}</div>
        <nav class="form-record-navigation justify-self-end" aria-label={lang === 'es' ? 'Navegación de registros' : 'Record navigation'}>
            {targets.map((target, direction) => target && model
                ? <a href={buildRecordUrl(model, target.uuid)} class="topbar-action-btn form-record-nav-btn" aria-label={labels[direction]}
                    data-form-nav={direction ? 'next' : 'previous'} key={direction}><Icon definition={direction ? faChevronRight : faChevronLeft} class="topbar-action-icon" /></a>
                : <button type="button" class="topbar-action-btn form-record-nav-btn" aria-label={labels[direction]} disabled
                    data-form-nav={direction ? 'next' : 'previous'} key={direction}><Icon definition={direction ? faChevronRight : faChevronLeft} class="topbar-action-icon" /></button>)}
            <span class="form-record-counter" aria-label={`${lang === 'es' ? 'Registro' : 'Record'} ${index + 1} ${lang === 'es' ? 'de' : 'of'} ${records.length}`}>
                <span class="form-record-counter-current">{index + 1}</span><span aria-hidden="true">/</span><span>{records.length}</span>
            </span>
        </nav>
    </footer>;
}

export function FormView({ data = {}, lang = 'en', options = {} }) {
    const sourceRecord = useMemo(() => getRecord(data, options.recordUuid, options.recordModel), [data, options.recordUuid, options.recordModel]);
    const [record, setRecord] = useState(sourceRecord);
    const dirtyValuesRef = useRef({});
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [followerStatus, setFollowerStatus] = useState('');
    const [modalOpen, setModalOpen] = useState(false);
    const [replyOpen, setReplyOpen] = useState(false);
    const readMessageRef = useRef('');
    useLayoutEffect(() => { setRecord(sourceRecord); dirtyValuesRef.current = {}; setEditing(false); setSaving(false); }, [sourceRecord]);
    const isMainModel = !options.recordModel || options.recordModel === data?.model?.name;
    const modelReadOnly = isMainModel && data?.model?.readonly === true;
    const schema = isMainModel ? (data?.model?.schema ?? []) : inferSchema(record);
    const layout = getFormLayout(schema);
    const followerField = followersField(schema);
    const context = { ...(data?.model ?? {}), modelUuid: data?.model?.uuid, tags: data?.model?.tags ?? [], record, followerStatus };
    const title = isMainModel ? (data?.model?.label?.[lang] ?? data?.model?.name ?? '') : (options.recordModel ?? record.model ?? '');
    const modelName = options.recordModel || record.model || data?.model?.name;
    const isMessage = modelName === 'system.message';
    const replyInitialValues = useMemo(() => isMessage ? {
        subject: { [lang]: `Re: ${localizedValue(record.subject, lang) || ''}` },
        to_users: record.from_user_id ? [record.from_user_id] : [],
        message: { [lang]: replyMessage(record, lang) },
    } : {}, [isMessage, lang, record]);
    useEffect(() => {
        if (!isMessage || !record.uuid || record.status === 'Read' || readMessageRef.current === String(record.uuid)) return;
        const isRecipient = (record.to_users ?? []).some((user) => String(user.uuid) === String(authSignal.value.uuid));
        if (!isRecipient) return;
        readMessageRef.current = String(record.uuid);
        void updateSystemModelRecord({ model: 'system.message', recordUuid: record.uuid, values: { status: 'Read' } })
            .then(() => {
                setRecord((current) => ({ ...current, status: 'Read' }));
                dashboardActions.updateModelRecord(record.uuid, { status: 'Read' });
                return refreshPendingCounts();
            })
            .catch((error) => console.error('Unable to mark message as read.', error));
    }, [isMessage, record.uuid, record.status, record.to_users]);
    const setValue = (name, value) => {
        if (name === 'followers') {
            const previous = Array.isArray(record.followers) ? record.followers : [];
            const model = options.recordModel || record.model || data?.model?.name;
            setRecord((current) => ({ ...current, followers: value }));
            if (!model || record.uuid == null) return;
            setFollowerStatus('saving');
            void updateSystemModelRecord({ model, recordUuid: record.uuid, values: { followers: value } })
                .then((patch) => {
                    const followers = patch?.followers ?? value;
                    setRecord((current) => ({ ...current, followers }));
                    dashboardActions.updateModelRecord(record.uuid, { followers });
                    setFollowerStatus('saved');
                    globalThis.setTimeout(() => setFollowerStatus((current) => current === 'saved' ? '' : current), 1500);
                })
                .catch((error) => {
                    setRecord((current) => ({ ...current, followers: previous }));
                    setFollowerStatus('error');
                    console.error('Unable to persist record followers.', error);
                    window.alert(lang === 'es' ? 'No se pudieron guardar los seguidores.' : 'Unable to save followers.');
                });
            return;
        }
        setRecord((current) => ({ ...current, [name]: value }));
        dirtyValuesRef.current = { ...dirtyValuesRef.current, [name]: value };
    };
    const saveRecord = async () => {
        if (!editing || saving) return;
        const values = dirtyValuesRef.current;
        if (Object.keys(values).length === 0) {
            setEditing(false);
            return;
        }
        const model = options.recordModel || record.model || data?.model?.name;
        if (!model || record.uuid == null) return;
        setSaving(true);
        try {
            await updateSystemModelRecord({ model, recordUuid: record.uuid, values });
            dashboardActions.updateModelRecord(record.uuid, values);
            dirtyValuesRef.current = {};
            setEditing(false);
        } catch (error) {
            window.alert(lang === 'es' ? 'No se pudo guardar el registro.' : 'Unable to save the record.');
            console.error('Unable to persist form record update.', error);
        } finally {
            setSaving(false);
        }
    };
    const labels = lang === 'es'
        ? { edit: 'Editar', save: isMessage ? 'Enviar' : 'Guardar', archive: 'Archivar', delete: 'Borrar' }
        : { edit: 'Edit', save: isMessage ? 'Send' : 'Save', archive: 'Archive', delete: 'Delete' };
    return <main id="dashboard-content" class="dash-content" role="main" aria-label="Form" data-form-root data-form-mode={editing ? 'edit' : 'readonly'}>
        <input type="hidden" data-uuid={record.uuid ?? ''} value={record.uuid ?? ''} />
        <ViewHeader title={title} lang={lang} onCreate={modelReadOnly ? undefined : () => setModalOpen(true)} />
        <div class="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
            <section data-form-record class="rounded-xl border border-[var(--dash-border)] bg-[var(--dash-surface)] shadow-[var(--dash-shadow)]">
                {!editing && schema.map((field) => <input type="hidden" name={field.name} value={typeof record[field.name] === 'object' ? '' : (record[field.name] ?? '')} key={`value-${field.name}`} />)}
                <div class="form-record-header flex gap-4 border-b border-[var(--dash-border)] px-5 py-4">
                    {layout.header.image && <div class="shrink-0" data-form-header="image"><FieldControl field={layout.header.image}
                        value={record[layout.header.image.name]} onChange={setValue} lang={lang} readOnly={!editing} context={context} /></div>}
                    <div class="form-record-header-main min-w-0 flex-1"><div class="form-record-title-row flex items-start justify-between gap-4">
                        <div class="min-w-0 flex-1" data-form-header="title">
                            {layout.header.title && <FieldControl field={layout.header.title} value={record[layout.header.title.name]}
                                onChange={setValue} lang={lang} readOnly={!editing} context={context} />}
                            {layout.header.subtitle && <div class="mt-1" data-form-header="subtitle"><FieldControl field={layout.header.subtitle}
                                value={record[layout.header.subtitle.name]} onChange={setValue} lang={lang} readOnly={!editing} context={context} /></div>}
                        </div>
                        {!modelReadOnly && <div class="form-record-actions flex items-center gap-2">
                            {isMessage && <Action definition={faPaperPlane} label={lang === 'es' ? 'Contestar' : 'Reply'}
                                data-message-reply onClick={() => setReplyOpen(true)} />}
                            <Action definition={faPen} label={labels.edit} data-form-edit aria-pressed={String(editing)} onClick={() => setEditing(true)} />
                            <Action definition={isMessage ? faPaperPlane : faFloppyDisk} label={labels.save} data-form-save disabled={!editing || saving} onClick={() => { void saveRecord(); }} />
                            <Action definition={faBoxArchive} label={labels.archive} data-form-archive />
                            <Action definition={faTrash} label={labels.delete} data-form-delete />
                        </div>}
                    </div></div>
                </div>
                <SchemaFormLayout schema={schema} record={record} setValue={setValue} lang={lang} context={context} readOnly={modelReadOnly || !editing} />
                <RecordFooter data={data} record={record} recordModel={options.recordModel} lang={lang}
                    followers={<One2manyFollowersField field={followerField} value={record.followers}
                        onChange={setValue} lang={lang} readOnly={modelReadOnly || !editing} context={context} />}
                    right={<FooterFields fields={layout.footerRight} record={record} setValue={setValue} lang={lang} context={context} readOnly={modelReadOnly || !editing} />} />
            </section>
            {!modelReadOnly && <CommunicationPanel lang={lang}
                modelName={options.recordModel || record.model || data?.model?.name}
                modelUuid={isMainModel ? data?.model?.uuid : undefined} recordUuid={record.uuid}
                users={followerField.options ?? []} />}
        </div>
        {!modelReadOnly && <CreateModal data={data} lang={lang} open={modalOpen} onClose={() => setModalOpen(false)} />}
        {replyOpen && <CreateModal data={data} lang={lang} open onClose={() => setReplyOpen(false)} initialValues={replyInitialValues} />}
    </main>;
}
