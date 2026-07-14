import { afterEach, describe, expect, it, vi } from 'vitest';

import { mountTopbar } from '../src/app/components/topbar.jsx';
import { dashboard } from '../src/app/pages/dashboard.js';
import {
    clearAuthSession,
    getAccessToken,
    isAuthenticated,
    setAuthSession,
    setCurrentUser,
} from '../src/app/store/authStore.js';

afterEach(() => {
    vi.unstubAllGlobals();
    clearAuthSession();
    document.body.innerHTML = '';
});

describe('authenticated navigation', () => {
    it('redirects unauthenticated dashboard visits to login', () => {
        document.body.innerHTML = '<div id="app"></div>';
        const router = {
            goTo: vi.fn(),
            trigger404: vi.fn(),
        };

        dashboard({ params: {}, pathname: '/dashboard' }, router);

        expect(router.goTo).toHaveBeenCalledWith('login');
        expect(document.getElementById('dashboard-topbar')).toBeNull();
    });

    it('clears the in-memory session and redirects when logging out', () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
            new Response(JSON.stringify({ data: { logout: true } }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            }),
        ));
        setAuthSession({ email: 'user@example.com', token: 'access-token' });
        const router = { goTo: vi.fn() };
        document.body.innerHTML = '<div id="topbar-root"></div>';
        mountTopbar(document.getElementById('topbar-root'), {
            lang: 'es',
            theme: 'light',
            pageTitle: 'Dashboard',
            router,
        });

        document.querySelector('[data-logout]').click();

        expect(isAuthenticated.value).toBe(false);
        expect(getAccessToken()).toBeNull();
        expect(router.goTo).toHaveBeenCalledWith('login');
    });

    it('refreshes the dashboard topbar when the current user avatar changes', async () => {
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network disabled in tests')));
        setAuthSession({ email: 'user@example.com', token: 'access-token' });
        setCurrentUser({ uuid: 'user-1', name: 'Ana Admin', email: 'ana@example.com' });
        document.body.innerHTML = '<div id="app"></div>';
        window.history.replaceState({}, '', '/dashboard');

        dashboard({ params: {}, pathname: '/dashboard' }, { goTo: vi.fn(), trigger404: vi.fn() });

        expect(document.querySelector('.topbar-user-btn img')).toBeNull();

        setCurrentUser({ avatarUrl: '/avatar-new.jpg' });

        await vi.waitFor(() => {
            expect(document.querySelector('.topbar-user-btn img')?.getAttribute('src')).toBe('/avatar-new.jpg');
        });
    });
});
