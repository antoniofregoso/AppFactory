import { describe, expect, it } from 'vitest';

import { searchSystemModels } from '../src/app/api/systemModel.js';


describe('searchSystemModels', () => {
    it('requests the typed response fields and returns the payload', async () => {
        let requestBody;
        const payload = {
            requestId: '12345678-1234-5678-1234-567812345678',
            status: 'FAILED',
            interpretedQuery: 'report',
            needsClarification: false,
            clarificationQuestion: null,
            results: [],
            errors: [{ code: 'TIMEOUT', message: 'Timed out', model: null, field: null }],
        };
        const fetchImpl = async (_url, options) => {
            requestBody = JSON.parse(options.body);
            return new Response(JSON.stringify({ data: { systemSearch: payload } }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            });
        };

        const response = await searchSystemModels(
            { query: 'report', lang: 'en', limit: 10 },
            fetchImpl,
        );

        expect(response).toEqual(payload);
        expect(requestBody.query).toContain('requestId');
        expect(requestBody.query).toContain('needsClarification');
        expect(requestBody.query).toContain('clarificationQuestion');
        expect(requestBody.query).toContain('errors');
        expect(requestBody.variables).toEqual({
            input: { query: 'report', lang: 'en', limit: 10, mode: 'AUTO' },
        });
    });
});
