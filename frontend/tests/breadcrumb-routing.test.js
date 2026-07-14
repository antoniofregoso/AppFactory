import { beforeEach, describe, expect, it } from 'vitest';

import { getRecordBreadcrumbs, rememberRecordBreadcrumb, setRecordBreadcrumbs } from '../src/app/utils/routing.js';

describe('record breadcrumb routing', () => {
    beforeEach(() => {
        sessionStorage.clear();
        window.history.replaceState({}, '', '/dashboard/configuration/system.app/app-1');
    });

    it('stores a growing trail for nested related-record navigation', () => {
        setRecordBreadcrumbs(window.location.pathname, [
            { label: 'Apps', url: '/dashboard/configuration/system.app' },
            { label: 'My App', url: '/dashboard/configuration/system.app/app-1' },
        ]);
        rememberRecordBreadcrumb('/dashboard/configuration/system.company/company-1', 'My Company');
        expect(getRecordBreadcrumbs('/dashboard/configuration/system.company/company-1')).toEqual([
            { label: 'Apps', url: '/dashboard/configuration/system.app' },
            { label: 'My App', url: '/dashboard/configuration/system.app/app-1' },
            { label: 'My Company', url: '/dashboard/configuration/system.company/company-1' },
        ]);

        window.history.replaceState({}, '', '/dashboard/configuration/system.company/company-1');
        rememberRecordBreadcrumb('/dashboard/configuration/system.currency/currency-1', 'Mexican Peso');
        expect(getRecordBreadcrumbs('/dashboard/configuration/system.currency/currency-1')).toEqual([
            { label: 'Apps', url: '/dashboard/configuration/system.app' },
            { label: 'My App', url: '/dashboard/configuration/system.app/app-1' },
            { label: 'My Company', url: '/dashboard/configuration/system.company/company-1' },
            { label: 'Mexican Peso', url: '/dashboard/configuration/system.currency/currency-1' },
        ]);
    });
});
