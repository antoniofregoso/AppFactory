import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const styles = readFileSync('src/style.css', 'utf8');

describe('dashboard scroll layout', () => {
    it('constrains the nested content root so each view can scroll vertically', () => {
        const rootRule = styles.match(/#dashboard-content-root\s*\{([^}]+)\}/)?.[1] ?? '';
        const contentRule = styles.match(/\.dash-content\s*\{([^}]+)\}/)?.[1] ?? '';

        expect(rootRule).toMatch(/flex:\s*1/);
        expect(rootRule).toMatch(/min-height:\s*0/);
        expect(rootRule).toMatch(/overflow:\s*hidden/);
        expect(contentRule).toMatch(/min-height:\s*0/);
        expect(contentRule).toMatch(/overflow-y:\s*auto/);
    });

    it('stretches the nested Preact sidebar to the viewport height', () => {
        const rootRule = styles.match(/#dashboard-sidebar-root\s*\{([^}]+)\}/)?.[1] ?? '';
        const sidebarRule = styles.match(/#dashboard-sidebar-root\s*>\s*\.sidebar\s*\{([^}]+)\}/)?.[1] ?? '';

        expect(rootRule).toMatch(/display:\s*flex/);
        expect(rootRule).toMatch(/align-self:\s*stretch/);
        expect(sidebarRule).toMatch(/height:\s*100%/);
    });
});
