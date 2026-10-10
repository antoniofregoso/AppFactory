import Sortable from 'sortablejs';
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { deleteSystemModelRecord, updateSystemModelRecord } from '../api/systemModel.js';
import { faArrowsRotate, faChevronLeft, faChevronRight, faTrash } from '../components/icon.js';
import { dashboardActions } from '../store/actions/index.js';
import { authSignal } from '../store/authStore.js';
import { hasModelActionPermission } from '../utils/accessControl.js';
import { buildRecordUrl } from '../utils/index.js';
import { CreateModal, Icon, ViewHeader } from './ViewPrimitives.jsx';

const HOUR_HEIGHT = 48;
const DEFAULT_EVENT_MINUTES = 24 * 60;
const MAX_RECURRENCE_STEPS = 20_000;
const PALETTE = {
    zinc: { bg: '#f4f4f5', border: '#71717a', text: '#3f3f46' }, red: { bg: '#fee2e2', border: '#dc2626', text: '#991b1b' },
    blue: { bg: '#dbeafe', border: '#2563eb', text: '#1d4ed8' }, purple: { bg: '#f3e8ff', border: '#9333ea', text: '#6b21a8' },
    green: { bg: '#d1fae5', border: '#059669', text: '#047857' }, orange: { bg: '#ffedd5', border: '#ea580c', text: '#c2410c' },
    yellow: { bg: '#fef9c3', border: '#ca8a04', text: '#854d0e' }, cyan: { bg: '#cffafe', border: '#0891b2', text: '#0e7490' },
    indigo: { bg: '#e0e7ff', border: '#4f46e5', text: '#4338ca' },
};
const locale = (lang) => lang === 'es' ? 'es-ES' : 'en-US';
const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());
const addDays = (date, count) => { const result = new Date(date); result.setDate(result.getDate() + count); return result; };
const startOfWeek = (date) => addDays(startOfDay(date), -((date.getDay() + 6) % 7));
const sameDay = (left, right) => left.getFullYear() === right.getFullYear() && left.getMonth() === right.getMonth() && left.getDate() === right.getDate();
const dayKey = (date) => `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
const parseDayKey = (value) => { const [year, month, day] = value.split('-').map(Number); return new Date(year, month, day); };
const formatTime = (date, lang) => date.toLocaleTimeString(locale(lang), { hour: '2-digit', minute: '2-digit' });

function parseDate(value) {
    if (!value) return null;
    if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : new Date(value);
    const date = new Date(String(value).trim().replace(' ', 'T').replace(/^(\d{4}-\d{2}-\d{2}):(\d{2}:\d{2}(?::\d{2})?)$/, '$1T$2'));
    return Number.isNaN(date.getTime()) ? null : date;
}

function calendarTitle(value, lang) {
    if (value == null) return '';
    if (typeof value !== 'object') return String(value);
    const named = value.name ?? value;
    return typeof named === 'object' ? String(named[lang] ?? named.en ?? named.es ?? '') : String(named);
}

function recurrenceRule(value) {
    const preset = {
        daily: ['days', 1], weekly: ['days', 7], biweekly: ['days', 14],
        monthly: ['months', 1], quarterly: ['months', 3], yearly: ['years', 1],
        weekdays: ['weekdays', 1],
    }[value];
    if (preset) return { unit: preset[0], interval: preset[1] };
    const customValue = String(value ?? '');
    const lastWeekday = customValue.match(/^custom:\s*(?:cada|every)\s+(?:ú(?:ltimo|ltima)|ultimo|ultima|last)\s+(domingo|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|sunday|monday|tuesday|wednesday|thursday|friday|saturday)\s*$/i);
    if (lastWeekday) {
        const weekdays = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
        const normalized = lastWeekday[1].toLocaleLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
        const weekday = weekdays.map((item) => item.normalize('NFD').replace(/\p{Diacritic}/gu, '')).indexOf(normalized) % 7;
        return { unit: 'last_weekday', interval: 1, weekday };
    }
    const custom = customValue.match(/^custom:\s*(?:cada|every)\s+(\d+)\s+(d[ií]as?|days?|semanas?|weeks?|mes(?:es)?|months?|a(?:ñ|n)os?|years?)\s*$/i);
    if (!custom) return null;
    const interval = Math.max(1, Number(custom[1]));
    const token = custom[2].toLocaleLowerCase();
    if (/semana|week/.test(token)) return { unit: 'days', interval: interval * 7 };
    if (/mes|month/.test(token)) return { unit: 'months', interval };
    if (/año|ano|year/.test(token)) return { unit: 'years', interval };
    return { unit: 'days', interval };
}

function occurrenceAt(start, rule, index) {
    const occurrence = new Date(start);
    if (index === 0) return occurrence;
    if (rule.unit === 'weekdays') {
        let remaining = index;
        while (remaining > 0) {
            occurrence.setDate(occurrence.getDate() + 1);
            if (occurrence.getDay() !== 0 && occurrence.getDay() !== 6) remaining -= 1;
        }
        return occurrence;
    }
    if (rule.unit === 'days') {
        occurrence.setDate(occurrence.getDate() + rule.interval * index);
        return occurrence;
    }
    if (rule.unit === 'months') {
        const day = occurrence.getDate();
        occurrence.setDate(1);
        occurrence.setMonth(occurrence.getMonth() + rule.interval * index);
        const daysInMonth = new Date(occurrence.getFullYear(), occurrence.getMonth() + 1, 0).getDate();
        if (day > daysInMonth) return null;
        occurrence.setDate(day);
        return occurrence;
    }
    if (rule.unit === 'last_weekday') {
        occurrence.setDate(1);
        occurrence.setMonth(occurrence.getMonth() + index + 1);
        occurrence.setDate(0);
        occurrence.setDate(occurrence.getDate() - ((occurrence.getDay() - rule.weekday + 7) % 7));
        return occurrence;
    }
    const month = occurrence.getMonth();
    const day = occurrence.getDate();
    occurrence.setDate(1);
    occurrence.setFullYear(occurrence.getFullYear() + rule.interval * index);
    occurrence.setMonth(month);
    const daysInMonth = new Date(occurrence.getFullYear(), month + 1, 0).getDate();
    if (day > daysInMonth) return null;
    occurrence.setDate(day);
    return occurrence;
}

function normalizedExceptions(values) {
    return new Set((Array.isArray(values) ? values : []).map((value) => parseDate(value)?.toISOString()).filter(Boolean));
}

export function toCalendarEvents(data = {}, lang = 'en', range = {}) {
    const schema = data?.model?.schema ?? [];
    const field = (key) => schema.find((item) => item?.calendar?.[key] === true);
    const startField = field('startDate');
    const endField = field('endDate');
    const titleField = field('title');
    const rangeStart = parseDate(range.start) ?? addDays(startOfDay(new Date()), -370);
    const rangeEnd = parseDate(range.end) ?? addDays(startOfDay(new Date()), 730);
    return (data.records ?? []).flatMap((record) => {
        const startsAt = parseDate(record[startField?.name]);
        if (!startsAt) return [];
        const parsedEnd = parseDate(record[endField?.name]);
        const hasExplicitEnd = Boolean(parsedEnd && parsedEnd > startsAt);
        const endsAt = hasExplicitEnd ? parsedEnd : new Date(startsAt.getTime() + DEFAULT_EVENT_MINUTES * 60_000);
        const duration = endsAt - startsAt;
        const status = (data?.model?.status ?? []).find((item) => item.value === record.status);
        const recordUuid = String(record.uuid ?? '');
        const rule = recurrenceRule(record.recurrence);
        const until = parseDate(record.recurrence_until);
        const exceptions = normalizedExceptions(record.recurrence_exceptions);
        const makeEvent = (occurrenceStart, recurring) => {
            const displayStart = hasExplicitEnd ? occurrenceStart : startOfDay(occurrenceStart);
            const displayEnd = hasExplicitEnd ? new Date(occurrenceStart.getTime() + duration) : addDays(displayStart, 1);
            return {
                id: recurring ? `${recordUuid}::${occurrenceStart.toISOString()}` : recordUuid,
                recordUuid,
                title: calendarTitle(record[titleField?.name], lang) || recordUuid,
                startsAt: displayStart,
                endsAt: displayEnd,
                occurrenceStart: occurrenceStart.toISOString(),
                seriesStartsAt: startsAt.toISOString(),
                hasExplicitEnd,
                isRecurring: Boolean(record.recurrence),
                recurrenceExpandable: Boolean(rule),
                recurrence: record.recurrence,
                recurrenceExceptions: [...exceptions],
                statusLabel: status?.[lang] ?? record.status ?? '',
                color: status?.color,
                href: data?.model?.name && record.uuid != null ? buildRecordUrl(data.model.name, record.uuid) : '',
            };
        };
        if (!rule) return [makeEvent(startsAt, false)];
        const occurrences = [];
        for (let index = 0; index < MAX_RECURRENCE_STEPS; index += 1) {
            const occurrenceStart = occurrenceAt(startsAt, rule, index);
            if (!occurrenceStart) continue;
            if (until && occurrenceStart > until) break;
            if (occurrenceStart >= rangeEnd) break;
            if (occurrenceStart < rangeStart || exceptions.has(occurrenceStart.toISOString())) continue;
            occurrences.push(makeEvent(occurrenceStart, true));
        }
        return occurrences;
    }).sort((a, b) => parseDate(a.occurrenceStart) - parseDate(b.occurrenceStart));
}

function eventStyle(color) {
    const value = PALETTE[color] ?? PALETTE.zinc;
    return { '--cal-event-bg': value.bg, '--cal-event-border': value.border, '--cal-event-text': value.text };
}

function eventsForDay(events, day) {
    const start = startOfDay(day);
    const end = addDays(start, 1);
    return events.filter((event) => event.startsAt < end && event.endsAt > start);
}

function Toolbar({ view, cursor, lang, onView, onNavigate, onPeriod }) {
    const monthName = cursor.toLocaleDateString(locale(lang), { month: 'long', year: 'numeric' });
    let title = monthName.charAt(0).toUpperCase() + monthName.slice(1);
    if (view === 'day') title = cursor.toLocaleDateString(locale(lang), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    if (view === 'week') {
        const start = startOfWeek(cursor); const end = addDays(start, 6);
        title = `${start.toLocaleDateString(locale(lang), { day: 'numeric', month: 'short' })} – ${end.toLocaleDateString(locale(lang), { day: 'numeric', month: 'short', year: 'numeric' })}`;
    }
    const labels = lang === 'es' ? { today: 'Hoy', month: 'Mes', week: 'Semana', day: 'Día' } : { today: 'Today', month: 'Month', week: 'Week', day: 'Day' };
    const years = Array.from({ length: 21 }, (_, index) => new Date().getFullYear() - 10 + index);
    return <div class="cal-toolbar"><div class="cal-toolbar-left">
        <button class="cal-today-btn" data-cal-nav="today" onClick={() => onNavigate('today')}>{labels.today}</button>
        <div class="cal-nav-group">
            <button class="cal-nav-btn" aria-label="Previous" onClick={() => onNavigate('prev')}><Icon definition={faChevronLeft} class="cal-nav-icon" /></button>
            <button class="cal-nav-btn" aria-label="Next" onClick={() => onNavigate('next')}><Icon definition={faChevronRight} class="cal-nav-icon" /></button>
        </div><h2 class="cal-title">{title}</h2>
    </div><div class="cal-toolbar-right"><div class="cal-period">
        <select class="cal-select" data-cal-month value={cursor.getMonth()} onChange={(event) => onPeriod(Number(event.currentTarget.value), cursor.getFullYear())}>
            {Array.from({ length: 12 }, (_, month) => <option value={month} key={month}>{new Date(2024, month, 1).toLocaleDateString(locale(lang), { month: 'long' })}</option>)}
        </select>
        <select class="cal-select" data-cal-year value={cursor.getFullYear()} onChange={(event) => onPeriod(cursor.getMonth(), Number(event.currentTarget.value))}>
            {years.map((year) => <option value={year} key={year}>{year}</option>)}
        </select></div><span class="cal-sep" aria-hidden="true" /><div class="cal-seg" role="group">
            {['month', 'week', 'day'].map((name) => <button class={`cal-seg-btn ${view === name ? 'cal-seg-btn--active' : ''}`}
                aria-pressed={String(view === name)} onClick={() => onView(name)} key={name}>{labels[name]}</button>)}
        </div></div></div>;
}

function EventTools({ event, lang, onDelete, canDelete }) {
    return <>
        {event.isRecurring && <span class="cal-event-recurring" aria-label={lang === 'es' ? 'Evento recurrente' : 'Recurring event'}><Icon definition={faArrowsRotate} /></span>}
        {canDelete && <button type="button" class="cal-event-delete" aria-label={lang === 'es' ? 'Borrar evento' : 'Delete event'}
            onClick={(click) => { click.preventDefault(); click.stopPropagation(); onDelete(event); }}><Icon definition={faTrash} /></button>}
    </>;
}

function MonthView({ cursor, events, lang, onDay, onMove, onDelete, readOnly = false, canDelete = false }) {
    const rootRef = useRef(null);
    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const gridStart = startOfWeek(first);
    const days = Array.from({ length: 42 }, (_, index) => addDays(gridStart, index));
    useEffect(() => {
        if (readOnly) return undefined;
        const instances = [...rootRef.current.querySelectorAll('.cal-month-events')].map((container) => Sortable.create(container, {
            group: { name: 'cal-month', pull: true, put: true }, animation: 150, draggable: '.cal-month-event:not(.cal-event--recurring)',
            ghostClass: 'cal-drag-ghost', chosenClass: 'cal-drag-chosen', dragClass: 'cal-drag-item',
            onAdd: (event) => onMove(event.item.dataset.eventId, parseDayKey(event.to.closest('[data-cal-day]').dataset.calDay), null),
        }));
        return () => instances.forEach((instance) => instance.destroy());
    }, [events, onMove, readOnly]);
    const weekdayStart = startOfWeek(new Date(2024, 0, 1));
    return <div class="cal-month" ref={rootRef}>
        <div class="cal-month-head">{Array.from({ length: 7 }, (_, index) => <div class="cal-month-dow" key={index}>{addDays(weekdayStart, index).toLocaleDateString(locale(lang), { weekday: 'short' })}</div>)}</div>
        <div class="cal-month-grid">{days.map((day) => {
            const dayEvents = eventsForDay(events, day);
            return <div class={`cal-month-cell ${day.getMonth() !== cursor.getMonth() ? 'cal-month-cell--muted' : ''}`} data-cal-day={dayKey(day)}
                onClick={(event) => { if (!event.target.closest('a')) onDay(day); }} key={dayKey(day)}>
                <span class={`cal-daynum ${sameDay(day, new Date()) ? 'cal-daynum--today' : ''}`}>{day.getDate()}</span>
                <div class="cal-month-events">{dayEvents.slice(0, 3).map((event) => <a href={event.href} class={`cal-month-event ${event.isRecurring ? 'cal-event--recurring' : ''}`} data-event-id={event.id}
                    style={eventStyle(event.color)} key={event.id}><span class="cal-event-time">{formatTime(event.startsAt, lang)}</span><span class="cal-event-title">{event.title}</span>
                    <EventTools event={event} lang={lang} onDelete={onDelete} canDelete={canDelete} /></a>)}
                    {dayEvents.length > 3 && <span class="cal-month-more">+{dayEvents.length - 3}</span>}
                </div>
            </div>;
        })}</div>
    </div>;
}

function TimeView({ days, events, lang, onDay, onMove, onResize, onDelete, readOnly = false, canDelete = false }) {
    const rootRef = useRef(null);
    useEffect(() => {
        if (readOnly) return undefined;
        const instances = [...rootRef.current.querySelectorAll('.cal-day-col')].map((container) => Sortable.create(container, {
            group: { name: 'cal-time', pull: true, put: true }, animation: 150, draggable: '.cal-time-event:not(.cal-event--recurring)',
            filter: '.cal-event-resize-handle', preventOnFilter: true,
            ghostClass: 'cal-drag-ghost', chosenClass: 'cal-drag-chosen', dragClass: 'cal-drag-item',
            onEnd: (event) => {
                const rect = event.to.getBoundingClientRect();
                const minutes = Math.round((Math.max(0, (event.originalEvent?.clientY ?? rect.top) - rect.top) / HOUR_HEIGHT) * 4) * 15;
                onMove(event.item.dataset.eventId, parseDayKey(event.to.dataset.calDay), Math.min(minutes, 1439));
            },
        }));
        return () => instances.forEach((instance) => instance.destroy());
    }, [events, onMove, readOnly]);
    const hours = Array.from({ length: 24 }, (_, hour) => hour);
    const nowTop = ((new Date().getHours() * 60 + new Date().getMinutes()) / 60) * HOUR_HEIGHT;
    const beginResize = (pointerEvent, event, day) => {
        pointerEvent.preventDefault();
        pointerEvent.stopPropagation();
        const column = pointerEvent.currentTarget.closest('.cal-day-col');
        const move = (eventPointer) => {
            const rect = column.getBoundingClientRect();
            const minutes = Math.round(((eventPointer.clientY - rect.top) / HOUR_HEIGHT) * 4) * 15;
            const end = new Date(day);
            end.setHours(0, Math.max(0, Math.min(minutes, 24 * 60)), 0, 0);
            onResize(event.id, end, false);
        };
        const end = (eventPointer) => {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', end);
            const rect = column.getBoundingClientRect();
            const minutes = Math.round(((eventPointer.clientY - rect.top) / HOUR_HEIGHT) * 4) * 15;
            const finalEnd = new Date(day);
            finalEnd.setHours(0, Math.max(0, Math.min(minutes, 24 * 60)), 0, 0);
            onResize(event.id, finalEnd, true);
        };
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', end);
    };
    return <div class="cal-time" style={{ '--cal-cols': days.length }} ref={rootRef}>
        <div class="cal-time-head"><div class="cal-corner" />{days.map((day) => <div class={`cal-col-head ${sameDay(day, new Date()) ? 'cal-col-head--today' : ''}`} key={dayKey(day)} onClick={() => onDay(day)}>
            <span class="cal-col-dow">{day.toLocaleDateString(locale(lang), { weekday: 'short' })}</span><span class={`cal-daynum ${sameDay(day, new Date()) ? 'cal-daynum--today' : ''}`}>{day.getDate()}</span>
        </div>)}</div>
        <div class="cal-time-body"><div class="cal-gutter">{hours.map((hour) => <div class="cal-hour-label" style={{ height: HOUR_HEIGHT }} key={hour}>{hour ? new Date(2024, 0, 1, hour).toLocaleTimeString(locale(lang), { hour: 'numeric' }) : ''}</div>)}</div>
            <div class="cal-cols">{days.map((day) => <div class={`cal-day-col ${sameDay(day, new Date()) ? 'cal-day-col--today' : ''}`} data-cal-day={dayKey(day)} key={dayKey(day)}>
                {hours.map((hour) => <div class="cal-hour-line" style={{ height: HOUR_HEIGHT }} key={hour} />)}
                {sameDay(day, new Date()) && <div class="cal-nowline" data-cal-nowline style={{ top: nowTop }}><span class="cal-nowdot" /></div>}
                {eventsForDay(events, day).map((event) => {
                    const start = event.startsAt < startOfDay(day) ? startOfDay(day) : event.startsAt;
                    const top = ((start.getHours() * 60 + start.getMinutes()) / 60) * HOUR_HEIGHT;
                    const height = Math.max(30, (Math.min(event.endsAt, addDays(startOfDay(day), 1)) - start) / 3_600_000 * HOUR_HEIGHT);
                    return <a href={event.href} class={`cal-time-event ${event.isRecurring ? 'cal-event--recurring' : ''}`} data-event-id={event.id} style={{ top, height, ...eventStyle(event.color) }} key={event.id}>
                        <span class="cal-time-event-hour">{formatTime(start, lang)}</span><span class="cal-time-event-title">{event.title}</span>{event.statusLabel && <span class="cal-time-event-status">{event.statusLabel}</span>}
                        <EventTools event={event} lang={lang} onDelete={onDelete} canDelete={canDelete} />
                        {!readOnly && !event.isRecurring && event.hasExplicitEnd && <span class="cal-event-resize-handle" aria-label={lang === 'es' ? 'Cambiar hora de fin' : 'Change end time'}
                            onClick={(eventClick) => { eventClick.preventDefault(); eventClick.stopPropagation(); }}
                            onPointerDown={(pointerEvent) => beginResize(pointerEvent, event, day)} />}
                    </a>;
                })}
            </div>)}</div>
        </div>
    </div>;
}

function calendarRange(cursor, view) {
    if (view === 'month') {
        const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
        const start = addDays(startOfWeek(first), -2);
        return { start, end: addDays(start, 46) };
    }
    const start = addDays(view === 'week' ? startOfWeek(cursor) : startOfDay(cursor), -2);
    return { start, end: addDays(start, view === 'week' ? 11 : 4) };
}

function DeleteEventDialog({ event, lang, busy, onChoose, onClose }) {
    if (!event) return null;
    const labels = lang === 'es'
        ? { title: 'Borrar evento', prompt: `¿Qué deseas borrar de “${event.title}”?`, one: 'Solo este evento', following: 'Este y los siguientes', all: 'Todos los eventos', cancel: 'Cancelar' }
        : { title: 'Delete event', prompt: `What would you like to delete from “${event.title}”?`, one: 'This event', following: 'This and following events', all: 'All events', cancel: 'Cancel' };
    return <div class="cal-dialog-backdrop" role="presentation" onClick={(click) => { if (click.target === click.currentTarget && !busy) onClose(); }}>
        <section class="cal-dialog" role="dialog" aria-modal="true" aria-labelledby="cal-delete-title">
            <h3 id="cal-delete-title">{labels.title}</h3><p>{event.isRecurring ? labels.prompt : event.title}</p>
            <div class="cal-dialog-actions">
                {event.recurrenceExpandable && <button type="button" data-delete-scope="one" disabled={busy} onClick={() => onChoose('one')}>{labels.one}</button>}
                {event.recurrenceExpandable && <button type="button" data-delete-scope="following" disabled={busy} onClick={() => onChoose('following')}>{labels.following}</button>}
                <button type="button" class="cal-dialog-danger" data-delete-scope="all" disabled={busy} onClick={() => onChoose('all')}>{event.isRecurring ? labels.all : labels.title}</button>
                <button type="button" data-delete-cancel disabled={busy} onClick={onClose}>{labels.cancel}</button>
            </div>
        </section>
    </div>;
}

export function CalendarView({ data = {}, lang = 'en' }) {
    const [view, setView] = useState('month');
    const [cursor, setCursor] = useState(() => startOfDay(new Date()));
    const [events, setEvents] = useState(() => toCalendarEvents(data, lang, calendarRange(new Date(), 'month')));
    const [modalOpen, setModalOpen] = useState(false);
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const modelName = data?.model?.name;
    const modelReadOnly = data?.model?.readonly === true;
    const canCreate = !modelReadOnly && hasModelActionPermission(modelName, 'create', authSignal.value.permissions);
    const readOnly = modelReadOnly || !hasModelActionPermission(modelName, 'update', authSignal.value.permissions);
    const canDelete = !modelReadOnly && hasModelActionPermission(modelName, 'delete', authSignal.value.permissions);
    useEffect(() => { setEvents(toCalendarEvents(data, lang, calendarRange(cursor, view))); }, [data, lang, cursor, view]);
    const navigate = (direction) => setCursor((current) => {
        if (direction === 'today') return startOfDay(new Date());
        const step = direction === 'prev' ? -1 : 1;
        if (view === 'month') return new Date(current.getFullYear(), current.getMonth() + step, 1);
        return addDays(current, step * (view === 'week' ? 7 : 1));
    });
    const schema = data?.model?.schema ?? [];
    const startField = schema.find((field) => field?.calendar?.startDate === true)?.name;
    const endField = schema.find((field) => field?.calendar?.endDate === true)?.name;
    const persistEvent = async (id, patch, rollback) => {
        dashboardActions.updateModelRecord(id, patch);
        try {
            await updateSystemModelRecord({ model: data?.model?.name, recordUuid: id, values: patch });
        } catch (error) {
            setEvents((current) => current.map((event) => event.id === id ? { ...event, ...rollback.event } : event));
            dashboardActions.updateModelRecord(id, rollback.record);
            console.error('Unable to persist calendar event update.', error);
        }
    };
    const moveEvent = (id, day, minutes) => setEvents((current) => current.map((event) => {
        if (event.id !== id) return event;
        const duration = event.endsAt - event.startsAt;
        const sourceStart = parseDate(event.occurrenceStart) ?? event.startsAt;
        const next = new Date(day);
        next.setHours(minutes == null ? sourceStart.getHours() : Math.floor(minutes / 60), minutes == null ? sourceStart.getMinutes() : minutes % 60, 0, 0);
        const displayStart = event.hasExplicitEnd ? next : startOfDay(next);
        const endsAt = event.hasExplicitEnd ? new Date(next.getTime() + duration) : addDays(displayStart, 1);
        const patch = { ...(startField ? { [startField]: next.toISOString() } : {}), ...(endField && event.hasExplicitEnd ? { [endField]: endsAt.toISOString() } : {}) };
        const record = data.records?.find((item) => String(item.uuid) === id) ?? {};
        void persistEvent(id, patch, { event: { startsAt: event.startsAt, endsAt: event.endsAt, occurrenceStart: event.occurrenceStart }, record: {
            ...(startField ? { [startField]: record[startField] } : {}), ...(endField && event.hasExplicitEnd ? { [endField]: record[endField] } : {}),
        } });
        return { ...event, startsAt: displayStart, endsAt, occurrenceStart: next.toISOString() };
    }));
    const resizeEvent = (id, end, commit) => setEvents((current) => current.map((event) => {
        if (event.id !== id) return event;
        if (end && end <= event.startsAt) return event;
        if (!commit && end) return { ...event, endsAt: end };
        if (commit && endField && end) {
            const record = data.records?.find((item) => String(item.uuid) === id) ?? {};
            void persistEvent(id, { [endField]: end.toISOString() }, {
                event: {
                    endsAt: parseDate(record[endField]) ?? new Date(event.startsAt.getTime() + DEFAULT_EVENT_MINUTES * 60_000),
                    hasExplicitEnd: Boolean(parseDate(record[endField])),
                },
                record: { [endField]: record[endField] },
            });
            return { ...event, endsAt: end, hasExplicitEnd: true };
        }
        return event;
    }));
    const deleteEvent = async (scope) => {
        const event = deleteTarget;
        if (!event || deleting) return;
        setDeleting(true);
        try {
            if (scope === 'all' || !event.recurrenceExpandable || (scope === 'following' && event.occurrenceStart === event.seriesStartsAt)) {
                await deleteSystemModelRecord({ model: modelName, recordUuid: event.recordUuid });
                dashboardActions.removeModelRecords([event.recordUuid]);
                setEvents((current) => current.filter((item) => item.recordUuid !== event.recordUuid));
            } else {
                const patch = scope === 'one'
                    ? { recurrence_exceptions: [...new Set([...event.recurrenceExceptions, event.occurrenceStart])] }
                    : { recurrence_until: new Date(parseDate(event.occurrenceStart).getTime() - 1).toISOString() };
                await updateSystemModelRecord({ model: modelName, recordUuid: event.recordUuid, values: patch });
                dashboardActions.updateModelRecord(event.recordUuid, patch);
                setEvents((current) => current.filter((item) => item.recordUuid !== event.recordUuid
                    || (scope === 'one' ? item.id !== event.id : parseDate(item.occurrenceStart) < parseDate(event.occurrenceStart))));
            }
            setDeleteTarget(null);
        } catch (error) {
            window.alert(lang === 'es' ? 'No se pudo borrar el evento.' : 'Unable to delete the event.');
            console.error('Unable to delete calendar event.', error);
        } finally {
            setDeleting(false);
        }
    };
    const days = useMemo(() => view === 'week' ? Array.from({ length: 7 }, (_, index) => addDays(startOfWeek(cursor), index)) : [startOfDay(cursor)], [view, cursor]);
    return <main id="dashboard-content" class="dash-content dash-content--calendar" role="main" aria-label="Calendar">
        <ViewHeader title={data?.model?.label?.[lang] ?? ''} count={events.length} lang={lang} class="cal-page-header"
            onCreate={canCreate ? () => setModalOpen(true) : undefined} />
        <div id="cal-root" class="cal"><Toolbar view={view} cursor={cursor} lang={lang} onView={setView} onNavigate={navigate}
            onPeriod={(month, year) => setCursor(new Date(year, month, Math.min(cursor.getDate(), new Date(year, month + 1, 0).getDate())))} />
            {view === 'month' ? <MonthView cursor={cursor} events={events} lang={lang} onDay={(day) => { setCursor(day); setView('day'); }} onMove={moveEvent} onDelete={setDeleteTarget} readOnly={readOnly} canDelete={canDelete} />
                : <TimeView days={days} events={events} lang={lang} onDay={(day) => { setCursor(day); setView('day'); }}
                    onMove={moveEvent} onResize={resizeEvent} onDelete={setDeleteTarget} readOnly={readOnly} canDelete={canDelete} />}
        </div>
        {canCreate && <CreateModal data={data} lang={lang} open={modalOpen} onClose={() => setModalOpen(false)} />}
        <DeleteEventDialog event={deleteTarget} lang={lang} busy={deleting} onChoose={(scope) => { void deleteEvent(scope); }} onClose={() => setDeleteTarget(null)} />
    </main>;
}
