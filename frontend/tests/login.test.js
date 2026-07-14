import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { login } from '../src/app/pages/login.jsx';
import {
    clearAuthSession,
    getAccessToken,
} from '../src/app/store/authStore.js';

function fillLoginForm(email = 'user@example.com', password = 'password123') {
    const form = document.querySelector('[data-login-form]');
    form.elements.email.value = email;
    form.elements.password.value = password;
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    return form;
}

describe('login page', () => {
    beforeEach(() => {
        const values = new Map();
        vi.stubGlobal('localStorage', {
            clear: () => values.clear(),
            getItem: (key) => values.get(key) ?? null,
            removeItem: (key) => values.delete(key),
            setItem: (key, value) => values.set(key, String(value)),
        });
        document.body.innerHTML = '<div id="app"></div>';
        localStorage.clear();
        clearAuthSession();
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        document.body.innerHTML = '';
        clearAuthSession();
    });

    it('authenticates, keeps the token in memory and navigates to dashboard', async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify({
                data: {
                    login: {
                        email: 'user@example.com',
                        token: 'access-token',
                    },
                },
            }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            }),
        );
        vi.stubGlobal('fetch', fetchMock);
        const router = { goTo: vi.fn() };

        login({}, router);
        fillLoginForm();

        await vi.waitFor(() => expect(router.goTo).toHaveBeenCalledWith('dash'));
        expect(getAccessToken()).toBe('access-token');
        expect(localStorage.getItem('dashboard_state') ?? '').not.toContain(
            'access-token',
        );

        const [, request] = fetchMock.mock.calls[0];
        expect(JSON.parse(request.body).variables).toEqual({
            login: {
                email: 'user@example.com',
                password: 'password123',
            },
        });
    });

    it('shows a generic error and stays on login when credentials fail', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
            new Response(
                JSON.stringify({ errors: [{ message: 'Invalid credentials' }] }),
                {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                },
            ),
        ));
        const router = { goTo: vi.fn() };

        login({}, router);
        const form = fillLoginForm();

        await vi.waitFor(() => {
            expect(form.querySelector('[data-login-error]').hidden).toBe(false);
        });
        expect(router.goTo).not.toHaveBeenCalled();
        expect(getAccessToken()).toBeNull();
    });

    it('does not blame credentials when the authentication service fails', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
            new Response(
                JSON.stringify({ errors: [{ message: 'Database connection failed' }] }),
                {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                },
            ),
        ));
        const router = { goTo: vi.fn() };

        login({}, router);
        const form = fillLoginForm();

        await vi.waitFor(() => {
            expect(form.querySelector('[data-login-error]').textContent).toContain(
                'authentication service is unavailable',
            );
        });
        expect(form.querySelector('[data-login-error]').textContent).not.toContain(
            'email or password is incorrect',
        );
        expect(router.goTo).not.toHaveBeenCalled();
    });

    it('shows and hides the password accessibly', () => {
        const router = { goTo: vi.fn() };
        login({}, router);
        const password = document.querySelector('[name="password"]');
        const toggle = document.querySelector('[data-password-toggle]');

        expect(password.type).toBe('password');
        expect(toggle.getAttribute('aria-pressed')).toBe('false');

        toggle.click();
        expect(password.type).toBe('text');
        expect(toggle.getAttribute('aria-pressed')).toBe('true');
        expect(toggle.getAttribute('aria-label')).toBe('Hide password');

        toggle.click();
        expect(password.type).toBe('password');
        expect(toggle.getAttribute('aria-pressed')).toBe('false');
        expect(toggle.getAttribute('aria-label')).toBe('Show password');
    });

    it('links the brand to the home page', () => {
        login({}, { goTo: vi.fn() });

        const brand = document.querySelector('.login-brand');
        expect(brand.tagName).toBe('A');
        expect(brand.getAttribute('href')).toBe('/');
        expect(brand.getAttribute('aria-label')).toBe('WebApp home');
    });
});
