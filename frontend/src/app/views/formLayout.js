function indexedField(field, index, value) {
    const position = Number(value);
    return Number.isFinite(position) ? { field, position, index } : null;
}

function sortFields(fields) {
    return fields.sort((left, right) => left.position - right.position || left.index - right.index);
}

/** Builds the header, columns and tabs declared by each field's form metadata. */
export function getFormLayout(schema = []) {
    const layout = {
        header: { image: null, title: null, subtitle: null },
        leftColumn: [],
        rightColumn: [],
        footerLeft: [],
        footerRight: [],
        tabs: [],
    };
    const tabGroups = new Map();

    schema.forEach((field, index) => {
        const config = field?.form;
        if (!config) return;
        const headerSlot = String(config.header ?? '').toLowerCase();
        if (Object.hasOwn(layout.header, headerSlot)) {
            layout.header[headerSlot] ??= field;
            return;
        }
        for (const area of ['leftColumn', 'rightColumn']) {
            const item = indexedField(field, index, config[area]);
            if (item) {
                layout[area].push(item);
                return;
            }
        }
        const footer = String(config.footer ?? '').toLowerCase();
        if (footer === 'left' || footer === 'right') {
            layout[footer === 'left' ? 'footerLeft' : 'footerRight'].push({ field, position: index, index });
            return;
        }
        const tab = indexedField(field, index, config.tab);
        if (!tab) return;
        if (!tabGroups.has(tab.position)) tabGroups.set(tab.position, []);
        tabGroups.get(tab.position).push(tab);
    });

    sortFields(layout.leftColumn);
    sortFields(layout.rightColumn);
    sortFields(layout.footerLeft);
    sortFields(layout.footerRight);
    layout.tabs = [...tabGroups.entries()]
        .sort(([left], [right]) => left - right)
        .map(([position, fields]) => ({ position, fields: sortFields(fields) }));
    return layout;
}

export function createEmptyRecord(schema = []) {
    return schema.reduce((record, field) => {
        record[field.name] = Object.hasOwn(field, 'default')
            ? field.default
            : field.type === 'boolean' ? false : field.type.startsWith('many2many') ? [] : '';
        return record;
    }, { uuid: '', name: '' });
}
