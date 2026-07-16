import { afterEach, describe, expect, it, vi } from 'vitest';
import { act } from 'preact/test-utils';
import { render } from 'preact';

const api = vi.hoisted(() => ({ create: vi.fn(), fetchView: vi.fn() }));

vi.mock('../src/app/api/systemModel.js', () => ({
    createSystemModelRecord: api.create,
    fetchSystemModelView: api.fetchView,
}));

import { SchemaFormLayout } from '../src/app/views/ViewPrimitives.jsx';

const parent = {
    uuid: 'system-1',
    model: 'talent.system',
    name: { es_MX: 'Desempeño' },
    areas: [],
};

const areaView = {
    model: {
        name: 'talent.area',
        label: { es: 'Área', en: 'Area' },
        schema: [
            { name: 'name', type: 'string_i18n', label: { es: 'Nombre' }, form: { header: 'title', required: true } },
            { name: 'code', type: 'string', label: { es: 'Clave' }, form: { header: 'subtitle', required: true } },
            { name: 'system_id', type: 'many2one', model: 'talent.system', label: { es: 'Sistema' }, form: { leftColumn: 0, required: true } },
        ],
    },
    records: [],
};

const parentSchema = [{
    name: 'areas',
    type: 'one2many_kanban',
    model: 'talent.area',
    label: { es: 'Áreas' },
    form: { tab: 0, view: 'one2many_kanban', kanban_view: { header: { title: 'name', subtitle: 'code' } } },
}];

afterEach(() => {
    render(null, document.body);
    document.body.innerHTML = '';
    vi.clearAllMocks();
});

describe('nested one2many creation', () => {
    it('creates a child from an empty kanban tab with the parent relation prefilled', async () => {
        api.fetchView.mockImplementation(({ model }) => Promise.resolve(model === 'talent.area'
            ? areaView
            : { model: { name: 'talent.system', schema: [] }, records: [parent] }));
        api.create.mockResolvedValue({ uuid: 'area-1', name: { es_MX: 'Ventas' }, code: 'SALES' });
        const onChildCreated = vi.fn();
        const host = document.createElement('div');
        document.body.appendChild(host);

        act(() => render(
            <SchemaFormLayout
                schema={parentSchema}
                record={parent}
                setValue={() => {}}
                onChildCreated={onChildCreated}
                lang="es"
                context={{ name: 'talent.system', record: parent }}
                readOnly
            />,
            host,
        ));

        expect(host.querySelector('[data-one2many-add="areas"]').textContent).toContain('Agregar');
        act(() => host.querySelector('[data-one2many-add="areas"]').click());
        await vi.waitFor(() => expect(host.querySelector('[data-form-modal]')).not.toBeNull());
        await vi.waitFor(() => expect(host.querySelector('select[name="system_id"]')?.disabled).toBe(false));

        const name = host.querySelector('input[name="name"]');
        name.value = 'Ventas';
        act(() => name.dispatchEvent(new Event('input', { bubbles: true })));
        const code = host.querySelector('input[name="code"]');
        code.value = 'SALES';
        act(() => code.dispatchEvent(new Event('input', { bubbles: true })));
        act(() => host.querySelector('button[aria-label="Guardar"]').click());

        await vi.waitFor(() => expect(api.create).toHaveBeenCalledWith({
            model: 'talent.area',
            values: {
                name: { es_MX: 'Ventas' },
                code: 'SALES',
                system_id: { uuid: 'system-1', model: 'talent.system', name: 'Desempeño' },
            },
        }));
        await vi.waitFor(() => expect(onChildCreated).toHaveBeenCalledWith(parentSchema[0], {
            uuid: 'area-1',
            name: { es_MX: 'Ventas' },
            code: 'SALES',
            model: 'talent.area',
        }));
    });
});
