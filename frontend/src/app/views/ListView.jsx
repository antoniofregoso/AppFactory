import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { deleteSystemModelRecord, updateSystemModelRecord } from '../api/systemModel.js';
import { FieldControl } from '../components/fields/index.js';
import { faBoxArchive, faGripVertical, faTrash } from '../components/icon.js';
import { NUMERIC_TYPES, buildRecordUrl, localizedValue } from '../utils/index.js';
import { rememberRecordBreadcrumb } from '../utils/routing.js';
import { makeSortable } from '../utils/sortable.js';
import { appSignal } from '../store/index.js';
import { dashboardActions } from '../store/actions/index.js';
import { CreateModal, Icon, ViewHeader } from './ViewPrimitives.jsx';

export function getListColumns(schema = []) {
    return schema.map((field, index) => ({ field, index }))
        .filter(({ field }) => field.list !== undefined && field.list !== false)
        .sort((a, b) => {
            const left = Number(typeof a.field.list === 'object' ? a.field.list.column : a.field.list);
            const right = Number(typeof b.field.list === 'object' ? b.field.list.column : b.field.list);
            return (Number.isFinite(left) ? left : Number.MAX_SAFE_INTEGER)
                - (Number.isFinite(right) ? right : Number.MAX_SAFE_INTEGER) || a.index - b.index;
        }).map(({ field }) => field);
}

function sortValue(field, value) {
    if (value == null || value === '') return '';
    if (field.type === 'many2one') return localizedValue(value?.name, 'en') ?? '';
    if (['monetary', 'decimal', 'integer', 'percentage'].includes(field.type)) return Number(value);
    if (field.type === 'boolean') return value ? 1 : 0;
    return String(localizedValue(value, 'en'));
}

function initialListSort(schema = []) {
    const field = schema.find((item) => ['asc', 'desc'].includes(item?.list?.order));
    return field ? { field: field.name, direction: field.list.order } : { field: '', direction: '' };
}

function Cell({ field, record, data, lang }) {
    const value = record[field.name];
    const isRelation = ['many2one', 'many2one_avatar'].includes(field.type);
    const isRecordTitle = !isRelation
        && (field.name === 'name' || String(field?.form?.header ?? '').toLowerCase() === 'title');
    if (isRecordTitle && value) {
        const href = buildRecordUrl(data?.model?.name, record.uuid);
        const label = localizedValue(value, lang);
        return <a href={href} onClick={() => rememberRecordBreadcrumb(href, label)}
            class="font-medium text-[var(--dash-accent)] hover:underline">{label}</a>;
    }
    return <FieldControl field={field} value={value} onChange={() => {}} lang={lang} readOnly
        context={{ ...(data?.model ?? {}), tags: data?.model?.tags ?? [], view: 'list' }} />;
}

function SortIcon({ direction }) {
    return <svg viewBox="0 0 8 10" class="h-2.5 w-2 shrink-0" fill="currentColor" aria-hidden="true">
        <path d="M4 0.5L7 4H1L4 0.5Z" opacity={direction === 'asc' ? 1 : 0.35} />
        <path d="M4 9.5L1 6H7L4 9.5Z" opacity={direction === 'desc' ? 1 : 0.35} />
    </svg>;
}

export function ListView({ data = {}, lang = 'en' }) {
    const [modalOpen, setModalOpen] = useState(false);
    const [selected, setSelected] = useState(() => new Set());
    const [recordPatches, setRecordPatches] = useState({});
    const [hiddenRecords, setHiddenRecords] = useState(() => new Set());
    const [sort, setSort] = useState(() => initialListSort(data?.model?.schema));
    const tbodyRef = useRef(null);
    const readOnly = data?.model?.readonly === true;
    const columns = useMemo(() => getListColumns(data?.model?.schema ?? []), [data?.model?.schema]);
    const records = useMemo(() => {
        const items = (data.records ?? [])
            .filter((record) => !hiddenRecords.has(String(record.uuid)))
            .map((record) => ({ ...record, ...(recordPatches[String(record.uuid)] ?? {}) }));
        const field = columns.find((item) => item.name === sort.field);
        if (!field || !sort.direction) return items;
        return items.sort((a, b) => {
            const left = sortValue(field, a[field.name]);
            const right = sortValue(field, b[field.name]);
            const result = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right));
            return sort.direction === 'asc' ? result : -result;
        });
    }, [data.records, columns, sort, recordPatches, hiddenRecords]);
    useEffect(() => {
        if (readOnly || !tbodyRef.current) return undefined;
        return makeSortable(tbodyRef.current, {
            handle: '.js-list-drag-handle',
            sortableOptions: { forceFallback: true, ghostClass: 'list-drag-ghost', chosenClass: 'list-drag-chosen', dragClass: 'list-drag-item' },
            onReorder: (ids) => {
                const full = appSignal.value.model?.records ?? data.records ?? [];
                if (!full.some((record) => Object.hasOwn(record, 'sequence'))) return;
                const visible = new Set(records.map((record) => String(record.uuid)));
                let index = 0;
                const reordered = full.map((record) => visible.has(String(record.uuid))
                    ? full.find((item) => String(item.uuid) === ids[index++])
                    : record);
                const previous = new Map(full.map((record) => [String(record.uuid), record.sequence]));
                reordered.forEach((record, position) => dashboardActions.updateModelRecord(record.uuid, { sequence: (position + 1) * 10 }));
                void Promise.all(reordered.map((record, position) => updateSystemModelRecord({
                    model: data?.model?.name, recordUuid: record.uuid, values: { sequence: (position + 1) * 10 },
                }))).catch((error) => {
                    previous.forEach((sequence, uuid) => dashboardActions.updateModelRecord(uuid, { sequence }));
                    console.error('Unable to persist list sequence.', error);
                });
            },
        });
    }, [data, records, readOnly]);
    const toggle = (uuid) => setSelected((current) => {
        const next = new Set(current);
        if (next.has(uuid)) next.delete(uuid); else next.add(uuid);
        return next;
    });
    const allSelected = records.length > 0 && records.every((record) => selected.has(String(record.uuid)));
    const setAll = (checked) => setSelected(checked ? new Set(records.map((record) => String(record.uuid))) : new Set());
    const archiveSelected = async () => {
        const selectedRecords = records.filter((record) => selected.has(String(record.uuid)));
        const model = data?.model?.name;
        const patchFor = (record) => model === 'system.message'
            ? { status: 'Archived' }
            : (Object.hasOwn(record, 'active') ? { active: false } : null);
        const changes = selectedRecords.map((record) => ({ record, patch: patchFor(record) })).filter((item) => item.patch);
        if (changes.length === 0) {
            window.alert(lang === 'es'
                ? 'Este modelo no tiene un campo active ni un estado Archived.'
                : 'This model has no active field or Archived status.');
            return;
        }
        setRecordPatches((current) => Object.fromEntries([
            ...Object.entries(current),
            ...changes.map(({ record, patch }) => [String(record.uuid), { ...(current[String(record.uuid)] ?? {}), ...patch }]),
        ]));
        changes.forEach(({ record, patch }) => dashboardActions.updateModelRecord(record.uuid, patch));
        try {
            await Promise.all(changes.map(({ record, patch }) => updateSystemModelRecord({
                model, recordUuid: record.uuid, values: patch,
            })));
            setSelected(new Set());
        } catch (error) {
            setRecordPatches((current) => {
                const next = { ...current };
                changes.forEach(({ record }) => { delete next[String(record.uuid)]; });
                return next;
            });
            changes.forEach(({ record, patch }) => dashboardActions.updateModelRecord(
                record.uuid,
                Object.fromEntries(Object.keys(patch).map((key) => [key, record[key]])),
            ));
            window.alert(lang === 'es' ? 'No se pudieron archivar los registros.' : 'Unable to archive records.');
            console.error('Unable to archive selected records.', error);
        }
    };
    const deleteSelected = async () => {
        const message = lang === 'es' ? '¿Borrar los registros seleccionados?' : 'Delete selected records?';
        if (!window.confirm(message)) return;
        const ids = [...selected];
        setHiddenRecords((current) => new Set([...current, ...ids]));
        setSelected(new Set());
        try {
            await Promise.all(ids.map((recordUuid) => deleteSystemModelRecord({ model: data?.model?.name, recordUuid })));
            dashboardActions.removeModelRecords(ids);
        } catch (error) {
            setHiddenRecords((current) => {
                const next = new Set(current);
                ids.forEach((id) => next.delete(String(id)));
                return next;
            });
            setSelected(new Set(ids));
            window.alert(lang === 'es' ? 'No se pudieron borrar los registros.' : 'Unable to delete records.');
            console.error('Unable to delete selected records.', error);
        }
    };
    const action = (definition, label, onClick) => <button type="button" class="topbar-action-btn" aria-label={label} data-tooltip={label} onClick={onClick}>
        <Icon definition={definition} class="topbar-action-icon" />
    </button>;
    return <main id="dashboard-content" class="dash-content" role="main" aria-label="List">
        <ViewHeader title={data?.model?.label?.[lang] ?? ''} count={data?.pagination?.total ?? records.length} lang={lang}
            actions={!readOnly && selected.size > 0 && <>
                {action(faTrash, lang === 'es' ? 'Borrar' : 'Delete', () => { void deleteSelected(); })}
                {action(faBoxArchive, lang === 'es' ? 'Archivar' : 'Archive', () => { void archiveSelected(); })}
            </>}
            onCreate={readOnly ? undefined : () => setModalOpen(true)} />
        <div class="w-full overflow-hidden rounded-xl border border-[var(--dash-border)] bg-[var(--dash-surface)] shadow-[var(--dash-shadow)]">
            {columns.length > 0 && records.length > 0 ? <div class="overflow-x-auto"><table class="w-full border-collapse text-sm">
                <thead><tr class="border-b border-[var(--dash-border)] bg-[var(--dash-surface-hover)]">
                    {!readOnly && <th class="w-10" aria-hidden="true" />}
                    {!readOnly && <th class="w-10 px-2 text-center align-middle"><input type="checkbox" checked={allSelected}
                        class="js-list-select-all h-4 w-4" aria-label={lang === 'es' ? 'Seleccionar todas las filas' : 'Select all rows'}
                        onChange={(event) => setAll(event.currentTarget.checked)} /></th>}
                    {columns.map((field) => {
                        const align = NUMERIC_TYPES.has(field.type) ? 'text-right' : 'text-left';
                        const direction = sort.field === field.name ? sort.direction : '';
                        return <th class={`${align} whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--dash-text-muted)]`} key={field.name}>
                            <span class="inline-flex items-center gap-0.5">{field.label?.[lang] ?? field.name}
                                {[true, 'asc', 'desc'].includes(field.list?.order) && <button type="button" class="js-list-sort ml-1 inline-flex" aria-label={`Sort by ${field.label?.[lang] ?? field.name}`}
                                    onClick={() => setSort({ field: field.name, direction: direction === 'asc' ? 'desc' : 'asc' })}><SortIcon direction={direction} /></button>}
                            </span>
                        </th>;
                    })}
                </tr></thead>
                <tbody ref={tbodyRef} data-list-rows>{records.map((record) => {
                    const uuid = String(record.uuid ?? '');
                    return <tr data-uuid={uuid} class={`border-b border-[var(--dash-border-soft)] last:border-0 hover:bg-[var(--dash-surface-hover)] ${selected.has(uuid) ? 'list-row--selected' : ''}`} key={uuid}>
                        {!readOnly && <td class="w-10 px-2 text-center"><button type="button" class="js-list-drag-handle inline-flex cursor-grab" aria-label="Reorder row"><Icon definition={faGripVertical} class="h-3.5 w-3.5" /></button></td>}
                        {!readOnly && <td class="w-10 px-2 text-center"><input type="checkbox" checked={selected.has(uuid)} class="js-list-row-select h-4 w-4"
                            aria-label={lang === 'es' ? 'Seleccionar fila' : 'Select row'} onChange={() => toggle(uuid)} /></td>}
                        {columns.map((field) => <td class={`${NUMERIC_TYPES.has(field.type) ? 'text-right' : 'text-left'} whitespace-nowrap px-4 py-2.5 text-[var(--dash-text)]`} key={field.name}>
                            <Cell field={field} record={record} data={data} lang={lang} />
                        </td>)}
                    </tr>;
                })}</tbody>
            </table></div> : <div class="px-5 py-10 text-center text-sm text-[var(--dash-text-muted)]">{lang === 'es' ? 'Sin registros' : 'No records'}</div>}
        </div>
        {!readOnly && <CreateModal data={data} lang={lang} open={modalOpen} onClose={() => setModalOpen(false)} />}
    </main>;
}
