import { describe, expect, it } from 'vitest';

import { renderPasswordReset } from '../src/app/components/renderPasswordReset.js';


describe('password reset page', () => {
    it('links the brand to the home page', () => {
        const container = document.createElement('div');
        container.innerHTML = renderPasswordReset('en');

        const brand = container.querySelector('.login-brand');
        expect(brand.tagName).toBe('A');
        expect(brand.getAttribute('href')).toBe('/');
        expect(brand.getAttribute('aria-label')).toBe('WebApp home');
    });
});
