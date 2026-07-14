import { afterEach, describe, expect, it, vi } from 'vitest';

import { home } from '../src/app/pages/home.jsx';

afterEach(() => {
    document.body.innerHTML = '';
});

describe('public home page', () => {
    it('renders navigation, hero, features and footer', () => {
        document.body.innerHTML = '<div id="app"></div>';
        home({}, { goTo: vi.fn() });

        expect(document.querySelector('.home-brand-logo')).not.toBeNull();
        expect(document.querySelector('.home-hero h1')).not.toBeNull();
        expect(document.querySelectorAll('.home-feature-grid article')).toHaveLength(3);
        expect(document.querySelector('.home-footer')).not.toBeNull();
        expect(document.querySelector('[aria-disabled="true"]').disabled).toBe(true);
    });

    it('navigates to login from the header and hero actions', () => {
        document.body.innerHTML = '<div id="app"></div>';
        const router = { goTo: vi.fn() };
        home({}, router);
        const loginButtons = document.querySelectorAll('[data-home-login]');

        expect(loginButtons).toHaveLength(2);
        loginButtons.forEach((button) => button.click());
        expect(router.goTo).toHaveBeenCalledTimes(2);
        expect(router.goTo).toHaveBeenLastCalledWith('login');
    });
});
