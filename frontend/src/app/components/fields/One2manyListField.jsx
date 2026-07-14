import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { locale, localizedValue } from '../../utils/ux.js';
import { FieldControl } from './FieldControl.jsx';

function itemHref(item) {
    return item?.model && item?.uuid != null ? buildRecordUrl(item.model, item.uuid) : '';
}

function cellValue(item, column) {
    return item?.[column.name];
}

function companyCurrency(items, context) {
    const company = context?.company ?? context?.record?.company ?? items.find((item) => item?.company)?.company;
    return company?.currency ?? company?.currency_id ?? context?.currency ?? {};
}

function monetaryTotal(value, items, context, lang) {
    const currency = companyCurrency(items, context);
    const symbol = currency?.symbol ?? context?.currencySymbol ?? '$';
    const position = currency?.position ?? 'BEFORE';
    const number = new Intl.NumberFormat(locale(lang), {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
    return position === 'AFTER' ? `${number} ${symbol}` : `${symbol}${number}`;
}

function aggregate(items, definition) {
    const values = items.map((item) => item?.[definition.name]);
    if (definition.type === 'count') {
        return values.filter((value) => value !== null && value !== undefined && value !== '').length;
    }
    if (definition.type === 'sum') {
        return values.reduce((total, value) => {
            const number = Number(value);
            return total + (Number.isFinite(number) ? number : 0);
        }, 0);
    }
    return null;
}

function Total({ definition, column, items, context, lang }) {
    if (!definition) return null;
    const value = aggregate(items, definition);
    if (value === null) return null;
    const formatted = column.type === 'monetary' ? monetaryTotal(value, items, context, lang) : value;
    const label = localizedValue(definition.label, lang);
    return <span class="font-semibold tabular-nums">{label && `${label}: `}{formatted}</span>;
}

function Cell({ item, column, lang, context }) {
    const value = cellValue(item, column);
    const href = column.name === 'name' ? itemHref(item) : '';

    if (href) {
        return (
            <a href={href} onClick={() => rememberRecordBreadcrumb(href, localizedValue(value, lang))}
                class="font-medium text-[var(--dash-accent)] hover:underline">
                {localizedValue(value, lang) || '—'}
            </a>
        );
    }

    return <FieldControl field={column} value={value} onChange={() => {}} lang={lang} readOnly context={context} />;
}

/** Tabular one2many rendering configured by the ordered fields in `field.form.list_view`. */
export function One2manyListField({ field, value, lang = 'en', context = {} }) {
    const items = Array.isArray(value) ? value : [];
    const columns = Array.isArray(field?.form?.list_view) ? field.form.list_view : [];
    const functions = Array.isArray(field?.form?.function) ? field.form.function : [];
    const functionByName = new Map(functions.map((definition) => [definition.name, definition]));

    if (items.length === 0 || columns.length === 0) {
        return <span class="text-[var(--dash-text-soft)]">—</span>;
    }

    return (
        <div class="overflow-x-auto rounded-lg border border-[var(--dash-border)]">
            <table class="w-full border-collapse text-left text-sm">
                <thead class="bg-[var(--dash-surface-hover)] text-[var(--dash-text-muted)]">
                    <tr>
                        {columns.map((column) => (
                            <th key={column.name} scope="col" class="px-3 py-2 font-medium">
                                {localizedValue(column.label, lang) || column.name}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody class="divide-y divide-[var(--dash-border)]">
                    {items.map((item, index) => (
                        <tr key={item?.uuid ?? item?.name ?? index} class="bg-[var(--dash-bg)]">
                            {columns.map((column) => (
                                <td key={column.name} class="px-3 py-2 align-middle text-[var(--dash-text)]">
                                    <Cell item={item} column={column} lang={lang} context={context} />
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
                {functions.length > 0 && (
                    <tfoot class="border-t border-[var(--dash-border)] bg-[var(--dash-surface-hover)] text-[var(--dash-text)]">
                        <tr>
                            {columns.map((column) => (
                                <td key={column.name} class="px-3 py-2 align-middle">
                                    <Total definition={functionByName.get(column.name)} column={column} items={items}
                                        context={context} lang={lang} />
                                </td>
                            ))}
                        </tr>
                    </tfoot>
                )}
            </table>
        </div>
    );
}
