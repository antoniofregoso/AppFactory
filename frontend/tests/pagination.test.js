import { afterEach, describe, expect, it } from 'vitest';

import { mountTopbar } from '../src/app/components/topbar.jsx';
import { appSignal } from '../src/app/store/appStore.js';
import { dashboardActions } from '../src/app/store/actions/dashboardActions.js';
import { normalizePagination, paginateData } from '../src/app/utils/pagination.js';

const originalState = structuredClone(appSignal.value);

afterEach(() => {
    appSignal.value = structuredClone(originalState);
});

describe('dashboard pagination', () => {
    it('uses per_page to slice records and calculate total pages', () => {
        const records = Array.from({ length: 50 }, (_, index) => ({ id: index + 1 }));
        const data = paginateData(
            { records },
            { page: 2, per_page: 20, total: records.length },
        );

        expect(data.records).toHaveLength(20);
        expect(data.records[0].id).toBe(21);
        expect(data.records.at(-1).id).toBe(40);
        expect(data.pagination.totalPages).toBe(3);
    });

    it('keeps per_page after normalization instead of falling back to 20', () => {
        const records = Array.from({ length: 25 }, (_, index) => ({ id: index + 1 }));
        const pagination = normalizePagination({ page: 2, per_page: 7, total: 25 });
        const data = paginateData({ records }, pagination);

        expect(data.records).toHaveLength(7);
        expect(data.records[0].id).toBe(8);
        expect(data.pagination.perPage).toBe(7);
    });

    it('clamps an invalid page to the available range', () => {
        expect(normalizePagination({ page: 9, per_page: 20, total: 50 }).page).toBe(3);
    });

    it('renders the current state and disables boundary controls', () => {
        document.body.innerHTML = '<div id="topbar-root"></div>';
        const container = document.getElementById('topbar-root');

        mountTopbar(container, {
            lang: 'en', theme: 'light', pageTitle: 'Sales',
            pagination: { page: 1, per_page: 20, total: 50 },
        });
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('1 / 3');
        expect(document.querySelector('.topbar-page-indicator').getAttribute('aria-label')).toBe('Page 1 of 3');
        expect(document.querySelector('[data-page-previous]').disabled).toBe(true);
        expect(document.querySelector('[data-page-next]').disabled).toBe(false);

        mountTopbar(container, {
            lang: 'en', theme: 'light', pageTitle: 'Sales',
            pagination: { page: 3, per_page: 20, total: 50 },
        });
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('3 / 3');
        expect(document.querySelector('.topbar-page-indicator').getAttribute('aria-label')).toBe('Page 3 of 3');
        expect(document.querySelector('[data-page-next]').disabled).toBe(true);
        expect(document.querySelector('[data-page-previous]').disabled).toBe(false);

        document.body.innerHTML = '';
    });

    it('moves through pages without exceeding total pages', () => {
        appSignal.value = {
            ...appSignal.value,
            dashboard: { view: 'list', page: 1, per_page: 20, total: 50 },
        };

        dashboardActions.nextPage();
        dashboardActions.nextPage();
        dashboardActions.nextPage();
        expect(appSignal.value.dashboard.page).toBe(3);

        dashboardActions.previousPage();
        expect(appSignal.value.dashboard.page).toBe(2);
    });
});
