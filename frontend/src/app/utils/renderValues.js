
import { formatCurrency, formatDate, formatDateTime } from './formatters';
import { localizedValue, resolveTags } from './ux.js';

export function renderValue(data, type, locale, currency, model, tagCatalog = []) {
    switch (type) {
        case 'string':
            return data?.[locale.slice(0, 2)] || data;
        case 'number':
            return data;
        case 'monetary':
            return `<span class="is-block has-text-right has-text-weight-semibold">${formatCurrency(data, locale, currency)}</span>`;
        case 'date':
            return formatDate(data, locale);
        case 'datetime':
            return formatDateTime(data, locale);
        case 'boolean':
            return data;
        case 'many2one':
            return `<a href="/model/${model}/${data.uuid}">${data.name?.[locale.slice(0, 2)] || data}</a>`;
        case 'many2one_avatar':
            return `<a href="/model/${model}/${data.uuid}"><figure class="image is-24x24"><img class="is-rounded" src="${data.avatar}" alt="${data.name?.[locale.slice(0, 2)] || data}" /></figure></a>`;
        case 'many2many':
            return data;
        case 'many2many_pills':
            const pillsData = groupPills(resolveTags(data, tagCatalog), locale);
            let pills = '<div class="field is-grouped is-grouped-multiline">';
            pillsData.forEach(item => {
                pills += `<button><div class="control"><div class="tags has-addons"><span class="tag ${item.color || ''}">${item.name}</span><span class="tag is-dark">${item.count}</span></div></div></button>`;
            });
            pills += '</div>';
            return pills;
        case 'one2many':
            return data;
        case null:
            return '-';
        case undefined:
            return '-';
        default:
            return data;
    }
}

function groupPills(data, locale) {
    const group = data.reduce((acc, item) => {
        const key = localizedValue(item.name, locale.slice(0, 2));
        if (!acc[key]) {
            acc[key] = {
                name: key,
                count: 0,
                color: item.color
            };
        }
        acc[key].count++;
        return acc;
    }, {});
    return Object.values(group);
}

export function viewIndicator(view) {
    let indicators = document.querySelectorAll('.view-selectors button');
    indicators.forEach(indicator => {
        indicator.classList.remove('is-active');
    });
    indicators.forEach(indicator => {
        if (indicator.dataset.action === view) {
            indicator.classList.add('is-active');
        }
    });
}
