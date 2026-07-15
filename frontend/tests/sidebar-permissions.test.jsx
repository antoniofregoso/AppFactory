import { describe, expect, it } from 'vitest';

import { hasMenuPermission, visibleMenuItems } from '../src/app/components/sidebar.jsx';

describe('sidebar permissions', () => {
    it('supports exact and hierarchical wildcard grants', () => {
        expect(hasMenuPermission(['system.user.manage'], 'system.user.manage')).toBe(true);
        expect(hasMenuPermission(['system.*'], 'system.user.manage')).toBe(true);
        expect(hasMenuPermission(['*'], 'access.manage')).toBe(true);
        expect(hasMenuPermission(['system.insight.read'], 'system.user.manage')).toBe(false);
    });

    it('filters submenu entries and removes an empty parent', () => {
        const menu = [{
            key: 'configuration',
            items: [
                { key: 'users', permission: 'system.user.manage' },
                { key: 'insights', permission: 'system.insight.read' },
            ],
        }];

        expect(visibleMenuItems(menu, ['system.insight.read'])[0].items.map((item) => item.key)).toEqual(['insights']);
        expect(visibleMenuItems(menu, ['talent.*'])).toEqual([]);
    });
});
