import { afterEach, describe, expect, it, vi } from 'vitest';

import { dashboard } from '../src/app/pages/dashboard.js';
import { appSignal } from '../src/app/store/appStore.js';
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
        // dashboard() kicks off a live schema fetch; keep it from hitting the network
        // and just let it fall back to the bundled demo schema, as it does offline.
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network disabled in tests')));
        setAuthSession({ email: 'user@example.com', token: 'access-token' });
        document.body.innerHTML = '<div id="app"></div>';
        window.history.replaceState({}, '', '/dashboard/area1');
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                active_area: 'area1',
                lang: 'en',
                theme: 'light',
            },
            dashboard: {
                view: 'form',
                page: 2,
                per_page: 20,
                total: 50,
            },
        };

        dashboard(
            { params: { area: 'area1' }, pathname: '/dashboard/area1' },
            { trigger404: vi.fn() },
        );

        expect(document.querySelector('[data-form-record] [name="name"]').value).toBe('SO-021');
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('2 / 3');

        document.querySelector('[data-page-next]').click();

        expect(appSignal.value.dashboard.page).toBe(3);
        expect(document.querySelector('[data-form-record] [name="name"]').value).toBe('SO-041');
        expect(document.querySelector('.topbar-page-indicator').textContent).toBe('3 / 3');
    });
});
