import { ClientError, GraphQLClient } from 'graphql-request';

import { refreshSession } from './auth.js';
import {
    clearAuthSession,
    getAccessToken,
    getAccessTokenExpiresAt,
    setAuthSession,
} from '../store/authStore.js';

const GRAPHQL_ENDPOINT = new URL(
    import.meta.env.VITE_GRAPHQL_ENDPOINT ?? '/graphql',
    globalThis.location?.origin ?? 'http://localhost',
).toString();
const REFRESH_EARLY_MS = 60_000;

let refreshPromise = null;
let authFailureHandler = redirectToLogin;

export function isAuthenticationError(error) {
    if (!(error instanceof ClientError)) return false;
    const status = error.response.status;
    if (status === 401) return true;
    return error.response.errors?.some(({ message = '', extensions = {} }) => (
        extensions.error_code === 'AUTHENTICATION_ERROR'
        || /not authenticated|unauthenticated|token expired|invalid token/i.test(message)
    )) ?? false;
}

export function accessTokenNeedsRefresh(now = Date.now()) {
    const expiresAt = getAccessTokenExpiresAt();
    return Number.isFinite(expiresAt) && expiresAt - now <= REFRESH_EARLY_MS;
}

function redirectToLogin() {
    if (globalThis.location?.pathname === '/login') return;
    globalThis.location?.assign?.('/login');
}

export function setAuthFailureHandler(handler = redirectToLogin) {
    authFailureHandler = handler;
}

async function refreshAuthSession(fetchImpl) {
    if (!refreshPromise) {
        refreshPromise = refreshSession(fetchImpl)
            .then((session) => {
                setAuthSession(session);
                return session;
            })
            .catch((error) => {
                clearAuthSession();
                authFailureHandler();
                throw error;
            })
            .finally(() => {
                refreshPromise = null;
            });
    }
    return refreshPromise;
}

async function ensureFreshAccessToken(fetchImpl) {
    if (accessTokenNeedsRefresh()) {
        await refreshAuthSession(fetchImpl);
    }
}

function createAuthenticatedClient(fetchImpl) {
    return new GraphQLClient(GRAPHQL_ENDPOINT, {
        credentials: 'include',
        fetch: fetchImpl,
        headers: () => {
            const token = getAccessToken();
            return token ? { Authorization: `Bearer ${token}` } : {};
        },
    });
}

export async function requestAuthenticated(
    query,
    variables,
    fetchImpl = globalThis.fetch,
) {
    await ensureFreshAccessToken(fetchImpl);
    const client = createAuthenticatedClient(fetchImpl);

    try {
        return await client.request(query, variables);
    } catch (error) {
        if (!isAuthenticationError(error)) throw error;
        await refreshAuthSession(fetchImpl);
        return client.request(query, variables);
    }
}

export async function requestAuthenticatedFetch(
    url,
    options = {},
    fetchImpl = globalThis.fetch,
) {
    await ensureFreshAccessToken(fetchImpl);
    const token = getAccessToken();
    const headers = new Headers(options.headers ?? {});
    if (token && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    let response = await fetchImpl(url, {
        ...options,
        headers,
        credentials: options.credentials ?? 'include',
    });
    if (response.status !== 401) return response;

    await refreshAuthSession(fetchImpl);
    const refreshedToken = getAccessToken();
    const retryHeaders = new Headers(options.headers ?? {});
    if (refreshedToken && !retryHeaders.has('Authorization')) {
        retryHeaders.set('Authorization', `Bearer ${refreshedToken}`);
    }
    response = await fetchImpl(url, {
        ...options,
        headers: retryHeaders,
        credentials: options.credentials ?? 'include',
    });
    return response;
}
