import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { localizedValue } from '../../utils/ux.js';
import { AuthenticatedImage } from '../AuthenticatedImage.jsx';
import { icon, faUser, faXmark } from '../icon.js';
import { isFieldReadOnly } from './fieldHelpers.js';

// Same palette as ColorField's default options, keyed by lowercase name for lookup.
const COLOR_HEX = {
    zinc: '#71717a', red: '#dc2626', blue: '#2563eb', purple: '#9333ea', green: '#16a34a',
    orange: '#ea580c', yellow: '#ca8a04', cyan: '#0891b2', indigo: '#4f46e5',
};

function accentColor(item) {
    const value = item?.color;
    if (!value) return null;
    return COLOR_HEX[String(value).toLowerCase()] ?? value;
}

function itemHref(item) {
    return item?.model && item?.uuid != null ? buildRecordUrl(item.model, item.uuid) : '';
}

function Avatar({ src, name }) {
    return src
        ? <AuthenticatedImage src={src} alt={name} class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--dash-border)]" />
        : (
            <span class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--dash-surface-hover)] text-[var(--dash-text-muted)] ring-1 ring-[var(--dash-border)]">
                <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faUser, 'h-3.5 w-3.5') }} />
            </span>
        );
}

function Card({ item, header, lang, onRemove }) {
    const title = header.title ? localizedValue(item?.[header.title], lang) : '';
    const subtitle = header.subtitle ? localizedValue(item?.[header.subtitle], lang) : '';
    const href = itemHref(item);
    const style = accentColor(item) ? { borderColor: accentColor(item) } : undefined;
    return (
        <article class="relative flex items-center gap-2 rounded-lg border border-[var(--dash-border)] bg-[var(--dash-bg)] p-2.5 shadow-sm" style={style}>
            {header.image && <Avatar src={item?.[header.image] ?? ''} name={title} />}
            <div class="min-w-0 flex-1">
                {title && (href
                    ? <a href={href} onClick={() => rememberRecordBreadcrumb(href, title)}
                        class="block truncate text-sm font-semibold text-[var(--dash-accent)] hover:underline">{title}</a>
                    : <span class="block truncate text-sm font-semibold text-[var(--dash-text)]">{title}</span>)}
                {subtitle && <span class="block truncate text-xs text-[var(--dash-text-muted)]">{subtitle}</span>}
            </div>
            {onRemove && (
                <button type="button" class="shrink-0 text-[var(--dash-text-soft)] hover:text-[var(--dash-text)]"
                    aria-label={lang === 'es' ? 'Quitar' : 'Remove'} onClick={onRemove}>
                    <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faXmark, 'h-3.5 w-3.5') }} />
                </button>
            )}
        </article>
    );
}

/** Mini-kanban rendering of a one2many relation, configured via `field.form.kanban_view.header`. */
export function One2manyKanbanField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const items = Array.isArray(value) ? value : [];
    const header = field?.form?.kanban_view?.header ?? {};
    const editable = !isFieldReadOnly(field, readOnly);

    if (items.length === 0) return <span class="text-[var(--dash-text-soft)]">—</span>;

    return (
        <div class="grid grid-cols-[repeat(auto-fill,minmax(14rem,1fr))] gap-2">
            {items.map((item, index) => (
                <Card item={item} header={header} lang={lang} key={item?.uuid ?? item?.name ?? index}
                    onRemove={editable ? () => onChange(field.name, items.filter((_, i) => i !== index)) : null} />
            ))}
        </div>
    );
}
