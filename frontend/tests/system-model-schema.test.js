import { describe, expect, it } from 'vitest';

import {
    SystemModelError,
    fetchSystemModelByName,
    fetchSystemModelView,
} from '../src/app/api/systemModel.js';
import { mapSystemModelToViewModel } from '../src/app/utils/systemModelSchema.js';

const SYSTEM_MODEL_RESPONSE = {
    uuid: '11111111-0000-4000-8000-000000000000',
    name: 'sale.order',
    schemas: [
        {
            uuid: '22222222-0000-4000-8000-000000000000',
            name: 'default',
            use: 'default',
            view: {
                groupBy: 'status',
                status: [{ value: 'draft', color: 'zinc', en: 'Draft', es: 'Borrador' }],
                schema: [
                    { name: 'name', type: 'string', label: { en: 'Order', es: 'Orden' } },
                ],
            },
        },
    ],
};

function jsonResponse(body) {
    return Promise.resolve(
        new Response(JSON.stringify(body), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
        }),
    );
}

describe('mapSystemModelToViewModel', () => {
    it('unwraps the requested schema.view into the flat model shape the views consume', () => {
        const model = mapSystemModelToViewModel(SYSTEM_MODEL_RESPONSE);

        expect(model).toEqual({
            name: 'sale.order',
            groupBy: 'status',
            status: [{ value: 'draft', color: 'zinc', en: 'Draft', es: 'Borrador' }],
            schema: [{ name: 'name', type: 'string', label: { en: 'Order', es: 'Orden' } }],
        });
    });

    it('throws when the requested "use" schema is missing', () => {
        expect(() => mapSystemModelToViewModel(SYSTEM_MODEL_RESPONSE, 'kanban')).toThrow(
            /has no schema for use "kanban"/,
        );
    });
});

describe('fetchSystemModelByName', () => {
    it('returns the systemModelByName payload on success', async () => {
        const fetchImpl = () => jsonResponse({ data: { systemModelByName: SYSTEM_MODEL_RESPONSE } });

        const result = await fetchSystemModelByName('sale.order', fetchImpl);

        expect(result).toEqual(SYSTEM_MODEL_RESPONSE);
    });

    it('wraps GraphQL errors in a SystemModelError', async () => {
        const fetchImpl = () =>
            jsonResponse({ data: null, errors: [{ message: 'Model not found' }] });

        await expect(fetchSystemModelByName('unknown.model', fetchImpl)).rejects.toThrow(
            SystemModelError,
        );
    });

    it('wraps network failures in a SystemModelError', async () => {
        const fetchImpl = () => Promise.reject(new Error('network down'));

        await expect(fetchSystemModelByName('sale.order', fetchImpl)).rejects.toThrow(
            SystemModelError,
        );
    });
});

describe('fetchSystemModelView', () => {
    it('requests a named insight schema with its selected period', async () => {
        let requestBody;
        const payload = {
            model: { name: 'system.insight', schema: { period: 'weekly' } },
            records: [],
        };
        const fetchImpl = async (_url, options) => {
            requestBody = JSON.parse(options.body);
            return new Response(JSON.stringify({ data: { systemModelView: payload } }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            });
        };

        const result = await fetchSystemModelView({
            model: 'system.insight',
            use: 'insight',
            name: 'userLogs',
            period: 'weekly',
        }, fetchImpl);

        expect(result).toEqual(payload);
        expect(requestBody.variables).toEqual({
            model: 'system.insight',
            use: 'insight',
            name: 'userLogs',
            period: 'weekly',
        });
    });
});
