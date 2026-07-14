import { afterEach, describe, expect, it, vi } from 'vitest';

import { dashboard, getInsightViewOptions } from '../src/app/pages/dashboard.js';
import { clearAuthSession, setAuthSession, setCurrentUser } from '../src/app/store/authStore.js';


afterEach(() => {
    clearAuthSession();
    dashboard({ params: {}, pathname: '/dashboard' }, { goTo: vi.fn(), trigger404: vi.fn() });
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
});


describe('named insight routing', () => {
    it('maps userLogs to its declarative schema query', () => {
        expect(getInsightViewOptions('userLogs')).toEqual({
            model: 'system.insight',
            use: 'insight',
            name: 'userLogs',
        });
    });

    it('rejects unknown and missing insight names', () => {
        expect(getInsightViewOptions('unknownInsight')).toBeNull();
        expect(getInsightViewOptions()).toBeNull();
    });

    it('loads and mounts the named insight returned by systemModelView', async () => {
        const insight = {
            period: 'today',
            layout: { graphics: 2 },
            kpis: [{
                id: 'kpiUsersOnline',
                name: { en: 'Online Users', es: 'Usuarios en línea' },
                value: 3,
                unit: 'Users',
                trend: 'up',
            }],
            gauges: [],
            graphics: [],
        };
        const fetchImpl = vi.fn(async (_url, options = {}) => {
            const body = options.body ? JSON.parse(options.body) : {};
            if (body.query?.includes('SystemModelView')) {
                return new Response(JSON.stringify({
                    data: {
                        systemModelView: {
                            model: {
                                name: 'system.insight',
                                schema: {
                                    ...insight,
                                    period: body.variables?.period ?? insight.period,
                                },
                            },
                            records: [],
                        },
                    },
                }), { status: 200, headers: { 'Content-Type': 'application/json' } });
            }
            return new Response(JSON.stringify({ data: {} }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            });
        });
        vi.stubGlobal('fetch', fetchImpl);
        setAuthSession({ email: 'admin@app.com', token: 'access-token' });
        setCurrentUser({ isAdmin: true, name: 'Admin' });
        document.body.innerHTML = '<div id="app"></div>';
        window.history.replaceState(
            {},
            '',
            '/dashboard/configuration/insights?v=userLogs',
        );

        dashboard(
            {
                params: { area: 'configuration', model: 'insights' },
                pathname: '/dashboard/configuration/insights',
            },
            { goTo: vi.fn(), trigger404: vi.fn() },
        );

        await vi.waitFor(() => {
            expect(document.querySelector('[data-insight-kpi-id="kpiUsersOnline"]'))
                .not.toBeNull();
        });
        expect(document.querySelector('[data-insight-period]').value).toBe('today');
        const modelViewRequest = fetchImpl.mock.calls
            .map(([, options]) => JSON.parse(options.body ?? '{}'))
            .find((body) => body.query?.includes('SystemModelView'));
        expect(modelViewRequest.variables).toEqual({
            model: 'system.insight',
            use: 'insight',
            name: 'userLogs',
            period: 'today',
        });

        const periodSelect = document.querySelector('[data-insight-period]');
        periodSelect.value = 'weekly';
        periodSelect.dispatchEvent(new Event('change', { bubbles: true }));

        await vi.waitFor(() => {
            const weeklyRequest = fetchImpl.mock.calls
                .map(([, options]) => JSON.parse(options.body ?? '{}'))
                .find((body) => (
                    body.query?.includes('SystemModelView')
                    && body.variables?.period === 'weekly'
                ));
            expect(weeklyRequest).toBeDefined();
        });
    });
});
