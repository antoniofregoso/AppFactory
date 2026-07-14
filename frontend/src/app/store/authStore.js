import { computed, signal } from '@preact/signals';

let accessToken = null;
let accessTokenExpiresAt = null;

export const authSignal = signal({
    uuid: null,
    email: null,
    name: null,
    avatarUrl: null,
    isAdmin: false,
    isAuthenticated: false,
});

export const isAuthenticated = computed(
    () => authSignal.value.isAuthenticated,
);

export function setAuthSession({ email, token, accessToken: nextAccessToken }) {
    accessToken = nextAccessToken ?? token;
    accessTokenExpiresAt = getTokenExpiration(accessToken);
    authSignal.value = {
        ...authSignal.value,
        email,
        isAuthenticated: Boolean(accessToken),
    };
}

/** Merges the authenticated user's profile (from the `me` query) into the session. */
export function setCurrentUser(profile = {}) {
    const { uuid, name, email, avatarUrl, isAdmin } = profile;
    const nextAvatarUrl = Object.hasOwn(profile, 'avatarUrl')
        ? avatarUrl
        : authSignal.value.avatarUrl;
    authSignal.value = {
        ...authSignal.value,
        uuid: uuid ?? authSignal.value.uuid,
        name: name ?? authSignal.value.name,
        email: email ?? authSignal.value.email,
        avatarUrl: nextAvatarUrl,
        isAdmin: isAdmin ?? authSignal.value.isAdmin,
    };
}

export function getAccessToken() {
    return accessToken;
}

export function getAccessTokenExpiresAt() {
    return accessTokenExpiresAt;
}

export function clearAuthSession() {
    accessToken = null;
    accessTokenExpiresAt = null;
    authSignal.value = {
        uuid: null,
        email: null,
        name: null,
        avatarUrl: null,
        isAdmin: false,
        isAuthenticated: false,
    };
}

function getTokenExpiration(token) {
    if (!token) return null;
    const [, payload] = token.split('.');
    if (!payload) return null;

    try {
        const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/');
        const decodedPayload = globalThis.atob(normalizedPayload);
        const { exp } = JSON.parse(decodedPayload);
        return Number.isFinite(exp) ? exp * 1000 : null;
    } catch {
        return null;
    }
}
