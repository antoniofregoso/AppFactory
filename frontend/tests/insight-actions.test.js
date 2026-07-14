import { beforeEach, describe, expect, it } from 'vitest';
import { appSignal } from '../src/app/store';
import { dashboardActions } from '../src/app/store/actions';
import { patchInsights, renderInsights } from '../src/app/views/renderInsights.js';

const initialInsights = {
    period: 'today',
    layout: { graphics: 3 },
    kpis: [{ id: 'revenue', name: 'Revenue', value: 10, trend: 'up' }],
    gauges: [{ id: 'efficiency', name: 'Efficiency', value: 70, max: 100 }],
    graphics: [{ id: 'sales', title: 'Sales', type: 'line', data: [1, 2] }],
};

describe('dashboard insight actions', () => {
    beforeEach(() => {
        appSignal.value = {
            ...appSignal.value,
            insights: structuredClone(initialInsights),
        };
    });

    it('updates one KPI by id without replacing unchanged collections', () => {
        const previousInsights = appSignal.value.insights;
        const previousGauges = previousInsights.gauges;
        const previousLayout = previousInsights.layout;

        dashboardActions.updateKpi('revenue', { value: 25 });

        expect(appSignal.value.insights).not.toBe(previousInsights);
        expect(appSignal.value.insights.kpis[0]).toMatchObject({
            id: 'revenue',
            name: 'Revenue',
            value: 25,
            trend: 'up',
        });
        expect(appSignal.value.insights.gauges).toBe(previousGauges);
        expect(appSignal.value.insights.layout).toBe(previousLayout);
    });

    it('supports updater functions and preserves the id', () => {
        dashboardActions.updateGauge('efficiency', (gauge) => ({
            id: 'ignored-id',
            value: gauge.value + 5,
        }));

        expect(appSignal.value.insights.gauges[0]).toMatchObject({
            id: 'efficiency',
            value: 75,
        });
    });

    it('updates the selected period', () => {
        dashboardActions.setInsightPeriod('monthly');
        expect(appSignal.value.insights.period).toBe('monthly');
    });

    it('refreshes indicator data without replacing dashboard configuration', () => {
        dashboardActions.refreshInsights({
            layout: { graphics: 1 },
            kpis: [{ id: 'revenue', name: 'Changed', value: 42 }],
            gauges: [{ id: 'efficiency', max: 999, value: 88 }],
            graphics: [{ id: 'sales', type: 'bar', title: 'Changed', data: [3, 4] }],
        });

        expect(appSignal.value.insights.layout).toEqual({ graphics: 3 });
        expect(appSignal.value.insights.kpis[0]).toMatchObject({
            name: 'Revenue',
            value: 42,
        });
        expect(appSignal.value.insights.gauges[0]).toMatchObject({
            name: 'Efficiency',
            max: 100,
            value: 88,
        });
        expect(appSignal.value.insights.graphics[0]).toMatchObject({
            title: 'Sales',
            type: 'line',
            data: [3, 4],
        });
    });

    it('rejects unknown ids and collections', () => {
        expect(() => dashboardActions.updateKpi('missing', { value: 1 }))
            .toThrow('Insight not found');
        expect(() => dashboardActions.updateInsight('unknown', 'sales', {}))
            .toThrow('Unknown insight collection');
        expect(() => dashboardActions.refreshInsights({
            kpis: [{ id: 'missing', value: 1 }],
        })).toThrow('Insight not found: kpis.missing');
    });
});

describe('differential insight rendering', () => {
    it('renders localized KPI units instead of coercing them to object strings', () => {
        const insights = {
            ...initialInsights,
            kpis: [{
                id: 'active-users',
                name: { en: 'Active Users', es: 'Usuarios activos' },
                value: 12,
                unit: { en: 'Users', es: 'Usuarios' },
                trend: 'up',
            }],
        };

        document.body.innerHTML = renderInsights(insights, 'en');
        expect(document.querySelector('.insight-kpi-value')?.textContent)
            .toBe('12 Users');

        document.body.innerHTML = renderInsights(insights, 'es');
        expect(document.querySelector('.insight-kpi-value')?.textContent)
            .toBe('12 Usuarios');
    });

    it('patches a KPI without replacing the insights container', () => {
        const previous = structuredClone(initialInsights);
        const next = {
            ...previous,
            kpis: previous.kpis.map((kpi) => ({ ...kpi, value: 42 })),
        };
        document.body.innerHTML = renderInsights(previous, 'en');
        const container = document.getElementById('dashboard-content');

        expect(patchInsights(previous, next, 'en')).toBe(true);
        expect(document.getElementById('dashboard-content')).toBe(container);
        expect(document.querySelector('[data-insight-kpi-id="revenue"] .insight-kpi-value')?.textContent)
            .toBe('42');
    });

    it('requests a full render when ids or collection structure change', () => {
        const previous = structuredClone(initialInsights);
        const next = { ...previous, kpis: [] };
        document.body.innerHTML = renderInsights(previous, 'en');

        expect(patchInsights(previous, next, 'en')).toBe(false);
    });
});
