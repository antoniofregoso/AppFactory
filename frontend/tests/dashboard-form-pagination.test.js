import { afterEach, describe, expect, it, vi } from 'vitest';

import { dashboard } from '../src/app/pages/dashboard.js';
import { appSignal } from '../src/app/store/appStore.js';
import { dashboardActions } from '../src/app/store/actions/index.js';
import {
    clearAuthSession,
    setAuthSession,
} from '../src/app/store/authStore.js';

afterEach(() => {
    clearAuthSession();
    document.body.innerHTML = '';
    vi.unstubAllGlobals();
});

describe('form view pagination', () => {
    it('shows the first record from the active page and reacts to page controls', () => {
        const modelView = {
            model: {
                name: 'system.app',
                label: { en: 'Applications' },
                schema: [{
                    name: 'name',
                    type: 'string',
                    label: { en: 'Name' },
                    form: { header: 'title' },
                }],
            },
            records: Array.from({ length: 50 }, (_, index) => ({
                uuid: `app-${index + 1}`,
                name: `APP-${String(index + 1).padStart(3, '0')}`,
            })),
        };
        vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
            data: { systemModelView: modelView },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } })));
        setAuthSession({ email: 'user@example.com', token: 'access-token' });
        document.body.innerHTML = '<div id="app"></div>';
        window.history.replaceState({}, '', '/dashboard/configuration/system.app');
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                active_area: 'configuration',
                lang: 'en',
                theme: 'light',
            },
            dashboard: {
                view: 'form',
                page: 2,
                per_page: 20,
                total: 50,
            },
            model: modelView,
        };

        dashboard(
            {
                params: { area: 'configuration', model: 'system.app' },
                pathname: '/dashboard/configuration/system.app',
            },
            { trigger404: vi.fn() },
        );
        dashboardActions.setView('form');
        dashboardActions.setPage(2);

        expect(document.querySelector('[data-form-record] [name="name"]').value).toBe('APP-021');
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('2 / 3');

        document.querySelector('[data-page-next]').click();

        expect(appSignal.value.dashboard.page).toBe(3);
        expect(document.querySelector('[data-form-record] [name="name"]').value).toBe('APP-041');
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('3 / 3');
    });
});
