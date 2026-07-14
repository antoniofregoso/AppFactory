import { afterEach, describe, expect, it } from 'vitest';
import { render } from 'preact';

import { FieldControl } from '../src/app/components/fields/index.js';
import { renderValue } from '../src/app/utils/renderValues.js';
import { mountKanban, mountList } from './helpers/mountView.jsx';

const tags = [{ uuid: 'tag-1', name: { en: 'Recurrent', es: 'Recurrente' }, color: 'green' }];
const data = {
    model: {
        name: 'sale.order', label: { en: 'Orders', es: 'Órdenes' }, tags,
        schema: [
            { name: 'name', type: 'string', list: { column: 0 }, kanban: { header: 'title' } },
            { name: 'tags', type: 'many2many_pills', list: { column: 1 }, kanban: { footer: 0 } },
        ],
    },
    records: [{ uuid: 'record-1', name: 'SO-001', tags: ['tag-1'] }],
};

afterEach(() => { document.body.innerHTML = ''; });

describe('localized tag names', () => {
    it.each([['list', mountList], ['kanban', mountKanban]])('renders the active language in the %s view', (_name, mount) => {
        const english = mount(data, 'en');
        expect(english.host.textContent).toContain('Recurrent');
        english.cleanup();
        document.body.innerHTML = '';
        const spanish = mount(data, 'es');
        expect(spanish.host.textContent).toContain('Recurrente');
        spanish.cleanup();
    });

    it('renders the active language in reusable form fields', () => {
        const host = document.createElement('div');
        render(<FieldControl field={data.model.schema[1]} value={['tag-1']} readOnly context={{ tags }} lang="es" />, host);
        expect(host.textContent).toContain('Recurrente');
    });

    it('renders localized pills through the shared value renderer', () => {
        expect(renderValue(['tag-1'], 'many2many_pills', 'en-US', null, null, tags)).toContain('Recurrent');
        expect(renderValue(['tag-1'], 'many2many_pills', 'es-MX', null, null, tags)).toContain('Recurrente');
    });
});
