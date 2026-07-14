import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { updateSystemModelRecord } from '../api/systemModel.js';
import { AuthenticatedImage } from '../components/AuthenticatedImage.jsx';
import { FieldControl } from '../components/fields/index.js';
import { faGripVertical, faPalette, faUser } from '../components/icon.js';
import { COLOR_CLASS, COLOR_FALLBACK, buildRecordUrl, localizedValue } from '../utils/index.js';
import { rememberRecordBreadcrumb } from '../utils/routing.js';
import { makeSortable } from '../utils/sortable.js';
import { dashboardActions } from '../store/actions/index.js';
import { appSignal } from '../store/index.js';
import { CreateModal, Icon, ViewHeader } from './ViewPrimitives.jsx';

function buildLayout(schema = []) {
    const layout = { image: null, title: null, subtitle: null, leftColumn: [], rightColumn: [], footer: [] };
    schema.forEach((field, index) => {
        const config = field.kanban;
        if (!config) return;
        const header = String(config.header ?? '').toLowerCase();
        if (Object.hasOwn(layout, header) && !Array.isArray(layout[header])) layout[header] = field;
        else for (const area of ['leftColumn', 'rightColumn', 'footer']) {
            const position = Number(config[area]);
            if (Number.isFinite(position)) layout[area].push({ field, position, index });
        }
    });
    for (const area of ['leftColumn', 'rightColumn', 'footer']) {
        layout[area].sort((a, b) => a.position - b.position || a.index - b.index);
    }
    return layout;
}

function normalizeColor(value) {
    return String(value ?? '').toLowerCase();
}

function colorHex(field, value) {
    if (!field || value == null || value === '') return null;
    const normalized = normalizeColor(value);
    return field.selection_values?.find((option) => normalizeColor(option.value) === normalized)?.hex ?? null;
}

function ColorPicker({ field, value, lang, onChange, onOpenChange }) {
    const [open, setOpen] = useState(false);
    const options = field?.selection_values ?? [];
    const selected = normalizeColor(value);
    if (options.length === 0) return null;

    return <div class="absolute bottom-1 right-1 z-10" data-kanban-color-picker>
        <button type="button"
            class="inline-flex size-5 items-center justify-center rounded text-[var(--dash-text-soft)] transition hover:bg-[var(--dash-surface-hover)] hover:text-[var(--dash-text)]"
            aria-label={lang === 'es' ? 'Cambiar color' : 'Change color'} aria-expanded={String(open)}
            onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                setOpen((current) => {
                    onOpenChange?.(!current);
                    return !current;
                });
            }}>
            <Icon definition={faPalette} class="size-3" />
        </button>
        {open && <div class="absolute bottom-full right-0 z-20 mb-1 grid w-max grid-cols-3 gap-0.5 rounded-md border border-[var(--dash-border)] bg-[var(--dash-surface)] p-1.5 shadow-lg"
            role="radiogroup" aria-label={lang === 'es' ? 'Color de la tarjeta' : 'Card color'}>
            {options.map((option) => {
                const checked = normalizeColor(option.value) === selected;
                const label = localizedValue(option.label, lang) || option.value;
                return <button type="button" key={option.value} role="radio" aria-checked={String(checked)} aria-label={label}
                    class={`block size-3 shrink-0 border-0 transition hover:scale-125 focus:outline-none ${checked ? 'z-10 scale-110 brightness-125 outline outline-1 outline-offset-1 outline-white' : ''}`}
                    style={{
                        backgroundColor: option.hex,
                        width: '0.75rem',
                        height: '0.75rem',
                        boxShadow: checked ? `0 0 7px 2px ${option.hex}` : 'none',
                    }}
                    onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        onChange(option.value);
                        setOpen(false);
                        onOpenChange?.(false);
                    }} />;
            })}
        </div>}
    </div>;
}

function Avatar({ src, name }) {
    return src
        ? <AuthenticatedImage src={src} alt={name} class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--dash-border)]" />
        : <span class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--dash-surface-hover)] text-[var(--dash-text-muted)] ring-1 ring-[var(--dash-border)]"><Icon definition={faUser} class="h-3.5 w-3.5" /></span>;
}

function Value({ field, value, lang, context }) {
    if (value == null || value === '') return null;
    return <FieldControl field={field} value={value} onChange={() => {}} lang={lang} readOnly context={context} />;
}

function Card({ record, layout, modelName, lang, context, colorField, onColorChange, readOnly }) {
    const [cardColor, setCardColor] = useState(colorField ? record[colorField.name] : null);
    const [pickerOpen, setPickerOpen] = useState(false);
    useEffect(() => setCardColor(colorField ? record[colorField.name] : null), [colorField, record]);
    const title = layout.title ? record[layout.title.name] : '';
    const titleText = localizedValue(title?.name ?? title, lang);
    const relatedAvatarField = [layout.title, layout.subtitle]
        .find((field) => field?.type === 'many2one_avatar');
    const relatedAvatar = relatedAvatarField
        ? record[relatedAvatarField.name]?.avatar
        : '';
    const avatar = layout.image ? record[layout.image.name] : relatedAvatar;
    const href = buildRecordUrl(modelName, record.uuid);
    const accentColor = colorHex(colorField, cardColor);
    const cardStyle = accentColor ? { borderColor: accentColor } : undefined;
    const column = (item) => {
        const value = record[item.field.name];
        if (value == null || value === '') return null;
        return <div class="flex items-baseline justify-between gap-1 text-xs" key={item.field.name}>
            <span class="text-[var(--dash-text-muted)]">{item.field.label?.[lang] ?? item.field.name}</span>
            <span class="font-medium text-[var(--dash-text)]"><Value field={item.field} value={value} lang={lang} context={context} /></span>
        </div>;
    };
    return (
        <article data-uuid={record.uuid ?? ''} data-color={cardColor ?? ''}
            class={`group relative rounded-lg border border-[var(--dash-border)] bg-[var(--dash-bg)] p-3 shadow-sm transition-shadow hover:shadow-md ${pickerOpen ? 'z-30' : ''}`} style={cardStyle}>
            <div class="flex items-start justify-between gap-2">
                <div class="flex min-w-0 items-center gap-2">
                    <Avatar src={avatar} name={titleText} />
                    <div class="flex min-w-0 flex-col gap-0.5">
                        {titleText && <a href={href} onClick={() => rememberRecordBreadcrumb(href, titleText)}
                            class="truncate text-sm font-semibold text-[var(--dash-accent)] hover:underline">{titleText}</a>}
                        {layout.subtitle && <span class="truncate text-xs text-[var(--dash-text-muted)]"><Value field={layout.subtitle}
                            value={record[layout.subtitle.name]} lang={lang} context={context} /></span>}
                    </div>
                </div>
                {!readOnly && <button type="button" class="js-kanban-drag-handle inline-flex shrink-0 cursor-grab items-center justify-center text-[var(--dash-text-soft)] hover:text-[var(--dash-text)]" aria-label="Reorder card">
                    <Icon definition={faGripVertical} class="h-3.5 w-3.5" />
                </button>}
            </div>
            {(layout.leftColumn.length > 0 || layout.rightColumn.length > 0) && <div class="mt-2 flex gap-2">
                <div class="flex flex-1 flex-col gap-1">{layout.leftColumn.map(column)}</div>
                <div class="flex flex-1 flex-col items-end gap-1">{layout.rightColumn.map(column)}</div>
            </div>}
            {layout.footer.length > 0 && <div class={`mt-2 flex items-end gap-2 ${colorField ? 'pr-4' : ''}`}>
                <div class="flex min-w-0 flex-1 flex-col gap-1">{layout.footer.map(({ field }) => {
                    const value = record[field.name];
                    return value == null || value === '' ? null : <div class="text-xs text-[var(--dash-text-muted)]" key={field.name}>
                        {field.type !== 'percentage' && <span>{field.label?.[lang] ?? field.name}: </span>}
                        <Value field={field} value={value} lang={lang} context={context} />
                    </div>;
                })}</div>
            </div>}
            {!readOnly && colorField && <ColorPicker field={colorField} value={cardColor} lang={lang}
                onOpenChange={setPickerOpen}
                onChange={(value) => { setCardColor(value); onColorChange(record.uuid, value); }} />}
        </article>
    );
}

function Cards({ records, groupValue, layout, modelName, lang, context, groupBy, colorField, onMove, onColorChange, readOnly }) {
    const ref = useRef(null);
    useEffect(() => readOnly ? undefined : makeSortable(ref.current, {
        handle: '.js-kanban-drag-handle',
        sortableOptions: { group: 'kanban', forceFallback: true, ghostClass: 'kanban-drag-ghost', chosenClass: 'kanban-drag-chosen', dragClass: 'kanban-drag-item' },
        onReorder: (_ids, event) => onMove(
            event.item?.dataset.uuid,
            event.to?.dataset.groupValue,
            [...(event.to?.children ?? [])].map((item) => item.dataset.uuid).filter(Boolean),
        ),
    }), [onMove, readOnly]);
    return <div ref={ref} data-kanban-cards data-group-value={groupValue}
        class={groupBy ? 'flex min-h-24 flex-col gap-2 p-2' : 'grid w-full grid-cols-[repeat(auto-fill,minmax(16rem,1fr))] gap-3'}>
        {records.map((record) => <Card record={record} layout={layout} modelName={modelName} lang={lang} context={context}
            colorField={colorField} onColorChange={onColorChange} readOnly={readOnly} key={record.uuid} />)}
    </div>;
}

export function KanbanView({ data = {}, lang = 'en' }) {
    const [modalOpen, setModalOpen] = useState(false);
    const [records, setRecords] = useState(data.records ?? []);
    const readOnly = data?.model?.readonly === true;
    useEffect(() => setRecords(data.records ?? []), [data.records]);
    const schema = data?.model?.schema ?? [];
    const layout = useMemo(() => buildLayout(schema), [schema]);
    const colorField = useMemo(() => schema.find((field) => field.type === 'color'), [schema]);
    const configured = data?.model?.groupBy;
    const groupBy = typeof configured === 'string' && configured.trim() ? configured.trim() : null;
    const groups = groupBy && Array.isArray(data?.model?.[groupBy]) ? data.model[groupBy] : [];
    const context = { ...(data?.model ?? {}), tags: data?.model?.tags ?? [] };
    const persistPatch = async (uuid, patch) => {
        const previous = records.find((record) => String(record.uuid) === String(uuid));
        if (!previous) return;
        const rollback = Object.fromEntries(Object.keys(patch).map((key) => [key, previous[key]]));
        setRecords((current) => current.map((record) => String(record.uuid) === String(uuid) ? { ...record, ...patch } : record));
        dashboardActions.updateModelRecord(uuid, patch);
        try {
            await updateSystemModelRecord({ model: data?.model?.name, recordUuid: uuid, values: patch });
        } catch (error) {
            setRecords((current) => current.map((record) => String(record.uuid) === String(uuid) ? { ...record, ...rollback } : record));
            dashboardActions.updateModelRecord(uuid, rollback);
            console.error('Unable to persist Kanban record update.', error);
        }
    };
    const onMove = (uuid, groupValue, destinationIds = []) => {
        const full = appSignal.value.model?.records ?? records;
        const localBefore = records;
        const visibleIds = new Set(records.map((record) => String(record.uuid)));
        const moved = full.find((record) => String(record.uuid) === String(uuid));
        if (!moved) return;
        const groupChanged = groupBy && groupValue != null
            && String(moved[groupBy]) !== String(groupValue);
        if (groupChanged) {
            void persistPatch(uuid, { [groupBy]: groupValue });
        }
        const withGroup = groupBy && groupValue != null
            ? full.map((record) => String(record.uuid) === String(uuid) ? { ...record, [groupBy]: groupValue } : record)
            : full;
        const destinationSet = new Set(destinationIds.map(String));
        const ordered = [];
        if (groupBy) {
            groups.forEach((group) => {
                const groupRecords = withGroup.filter((record) => String(record[groupBy]) === String(group.value));
                if (String(group.value) === String(groupValue)) {
                    destinationIds.forEach((id) => {
                        const record = groupRecords.find((item) => String(item.uuid) === String(id));
                        if (record) ordered.push(record);
                    });
                    ordered.push(...groupRecords.filter((record) => !destinationSet.has(String(record.uuid))));
                } else ordered.push(...groupRecords);
            });
        } else {
            destinationIds.forEach((id) => {
                const record = withGroup.find((item) => String(item.uuid) === String(id));
                if (record) ordered.push(record);
            });
            ordered.push(...withGroup.filter((record) => !destinationSet.has(String(record.uuid))));
        }
        const included = new Set(ordered.map((record) => String(record.uuid)));
        ordered.push(...withGroup.filter((record) => !included.has(String(record.uuid))));
        const previous = new Map(full.map((record) => [String(record.uuid), { sequence: record.sequence }]));
        const next = ordered.map((record, position) => ({ ...record, sequence: (position + 1) * 10 }));
        setRecords(next.filter((record) => visibleIds.has(String(record.uuid))));
        next.forEach((record) => dashboardActions.updateModelRecord(record.uuid, { sequence: record.sequence }));
        void Promise.all(next.map((record) => updateSystemModelRecord({
            model: data?.model?.name,
            recordUuid: record.uuid,
            values: { sequence: record.sequence },
        }))).catch((error) => {
            setRecords((current) => current.map((record) => {
                const old = localBefore.find((item) => String(item.uuid) === String(record.uuid));
                return old ? { ...record, sequence: old.sequence } : record;
            }));
            previous.forEach((patch, id) => dashboardActions.updateModelRecord(id, patch));
            console.error('Unable to persist Kanban sequence.', error);
        });
    };
    const onColorChange = (uuid, value) => {
        if (!colorField) return;
        void persistPatch(uuid, { [colorField.name]: value });
    };
    return <main id="dashboard-content" class="dash-content" role="main" aria-label="Kanban Board">
        <ViewHeader title={data?.model?.label?.[lang] ?? ''} count={data?.pagination?.total ?? records.length}
            lang={lang} onCreate={readOnly ? undefined : () => setModalOpen(true)} />
        <div class="-mt-16 flex items-start gap-4 overflow-x-auto pb-2 pt-16">
            {groupBy ? groups.map((group) => {
                const cards = records.filter((record) => String(record[groupBy]) === String(group.value));
                return <section class="flex min-w-64 flex-1 flex-col rounded-xl border border-[var(--dash-border)] bg-[var(--dash-surface)] shadow-[var(--dash-shadow)]" key={group.value}>
                    <header class="flex items-center justify-between gap-2 border-b border-[var(--dash-border)] px-3 py-2.5">
                        <span class={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${COLOR_CLASS[group.color] ?? COLOR_FALLBACK}`}>{group[lang] ?? group.value}</span>
                        <span data-kanban-count class="text-xs text-[var(--dash-text-muted)]">{cards.length}</span>
                    </header>
                    <Cards records={cards} groupValue={group.value} layout={layout} modelName={data?.model?.name ?? ''}
                        lang={lang} context={context} groupBy={groupBy} colorField={colorField} onMove={onMove} onColorChange={onColorChange} readOnly={readOnly} />
                </section>;
            }) : <Cards records={records} layout={layout} modelName={data?.model?.name ?? ''} lang={lang}
                context={context} groupBy={null} colorField={colorField} onMove={onMove} onColorChange={onColorChange} readOnly={readOnly} />}
        </div>
        {!readOnly && <CreateModal data={data} lang={lang} open={modalOpen} onClose={() => setModalOpen(false)} />}
    </main>;
}
