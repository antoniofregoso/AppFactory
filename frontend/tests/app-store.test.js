import { beforeEach, describe, expect, it, vi } from 'vitest';

const EMPTY_INSIGHTS = {
    period: 'today',
    kpis: [],
    gauges: [],
    graphics: [],
    layout: {},
};

describe('app store hydration', () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it('starts with empty insights instead of restoring stale persisted data', async () => {
        const savedState = {
            meta: { start: Date.now() },
            context: {},
            insights: {
                layout: { graphics: 99 },
                period: 'stale',
                kpis: [],
                gauges: [],
                graphics: [],
            },
        };
        const values = new Map([['dashboard_state', JSON.stringify(savedState)]]);
        vi.stubGlobal('localStorage', {
            getItem: (key) => values.get(key) ?? null,
            setItem: (key, value) => values.set(key, String(value)),
        });

        const { appSignal } = await import('../src/app/store/appStore.js');
        const { renderInsights } = await import('../src/app/views/renderInsights.js');

        expect(appSignal.value.insights).toEqual(EMPTY_INSIGHTS);
        expect(JSON.parse(values.get('dashboard_state'))).not.toHaveProperty('insights');
        document.body.innerHTML = renderInsights(appSignal.value.insights);
        expect(document.querySelector('[data-graphic-cols]')).toBeNull();
        expect(document.querySelector('.insight-empty')?.textContent.trim()).toBe('No KPIs');
    });
});
