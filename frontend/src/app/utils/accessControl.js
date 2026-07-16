const CONTROLLED_MODELS = new Set([
    'parties.party',
    'system.country',
    'system.country.state',
    'system.lang',
]);

export function hasPermission(permissions = [], requiredPermission) {
    if (!requiredPermission) return true;
    return permissions.some((grant) => {
        if (grant === '*' || grant === requiredPermission) return true;
        if (!grant.endsWith('.*')) return false;
        return requiredPermission.startsWith(grant.slice(0, -1));
    });
}

export function hasModelActionPermission(model, action, permissions = []) {
    if (!model) return true;
    if (!model.startsWith('talent.') && !CONTROLLED_MODELS.has(model)) return true;
    return hasPermission(permissions, `${model}.${action}`);
}
