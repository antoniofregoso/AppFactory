import { describe, expect, it } from 'vitest';

import { hasMenuPermission, MENU_ITEMS, visibleMenuItems } from '../src/app/components/sidebar.jsx';

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

    it('shows the complete access menu only to access managers', () => {
        const access = MENU_ITEMS.find((item) => item.key === 'access');

        expect(access.items.map((item) => item.key)).toEqual([
            'roles',
            'assignments',
            'permissions',
        ]);
        expect(visibleMenuItems([access], ['access.manage'])[0].items)
            .toHaveLength(3);
        expect(visibleMenuItems([access], ['system.*'])).toEqual([]);
    });

    it('limits the talent user to agents and gives the manager the full menu', () => {
        const talent = MENU_ITEMS.find((item) => item.key === 'talent');

        expect(visibleMenuItems([talent], [
            'talent.agent.read',
            'talent.agent.create',
            'talent.agent.update',
        ])[0].items.map((item) => item.key)).toEqual(['agents', 'config-talent']);
        expect(visibleMenuItems([talent], ['talent.*'])[0].items.map((item) => item.key))
            .toEqual(['agents', 'config-talent', 'systems', 'areas', 'positions']);
    });

    it('groups user activity and configuration under the users menu', () => {
        const users = MENU_ITEMS.find((item) => item.key === 'users');

        expect(visibleMenuItems([users], ['system.insight.read'])[0].items.map((item) => item.key))
            .toEqual(['insights', 'users_online']);
        expect(visibleMenuItems([users], ['system.user.manage'])[0].items.map((item) => item.key))
            .toEqual(['config-users', 'users']);
    });

    it('shows parties reference menus using their read grants', () => {
        const parties = MENU_ITEMS.find((item) => item.key === 'parties');
        const grants = [
            'parties.party.read',
            'system.country.read',
            'system.country.state.read',
            'system.lang.read',
        ];

        expect(visibleMenuItems([parties], grants)[0].items.map((item) => item.key))
            .toEqual(['parties', 'config-parties', 'countries', 'states', 'languages']);
    });
});
