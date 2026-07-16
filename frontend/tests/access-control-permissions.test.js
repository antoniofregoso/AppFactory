import { describe, expect, it } from 'vitest';

import { hasModelActionPermission, hasPermission } from '../src/app/utils/accessControl.js';

describe('model action permissions', () => {
    it('supports global, exact, and domain wildcard grants', () => {
        expect(hasPermission(['*'], 'talent.agent.delete')).toBe(true);
        expect(hasPermission(['talent.agent.update'], 'talent.agent.update')).toBe(true);
        expect(hasPermission(['talent.*'], 'talent.position.delete')).toBe(true);
        expect(hasPermission(['talent.agent.read'], 'talent.agent.delete')).toBe(false);
    });

    it('enforces actions on modular access-controlled models', () => {
        const talentUser = ['talent.agent.read', 'talent.agent.create', 'talent.agent.update'];
        expect(hasModelActionPermission('talent.agent', 'create', talentUser)).toBe(true);
        expect(hasModelActionPermission('talent.agent', 'delete', talentUser)).toBe(false);
        expect(hasModelActionPermission('talent.system', 'read', talentUser)).toBe(false);

        const partiesManager = ['parties.*', 'system.country.read', 'system.country.update'];
        expect(hasModelActionPermission('parties.party', 'delete', partiesManager)).toBe(true);
        expect(hasModelActionPermission('system.country', 'update', partiesManager)).toBe(true);
        expect(hasModelActionPermission('system.country', 'delete', partiesManager)).toBe(false);
    });

    it('keeps models outside modular RBAC on their existing policy', () => {
        expect(hasModelActionPermission('system.currency', 'delete', [])).toBe(true);
    });
});
