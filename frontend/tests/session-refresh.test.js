import { afterEach, describe, expect, it, vi } from 'vitest';

import {
    requestAuthenticated,
    setAuthFailureHandler,
} from '../src/app/api/session.js';
import {
    clearAuthSession,
    getAccessToken,
    isAuthenticated,
    setAuthSession,
} from '../src/app/store/authStore.js';

const QUERY = `query Protected { me { email } }`;

function tokenExpiringIn(seconds) {
    const payload = globalThis.btoa(JSON.stringify({
        exp: Math.floor(Date.now() / 1000) + seconds,
    }));
    return `header.${payload}.signature`;
}

function jsonResponse(body, status = 200) {
    return Promise.resolve(
        new Response(JSON.stringify(body), {
            status,
            headers: { 'Content-Type': 'application/json' },
        }),
    );
}

function isRefreshRequest(request) {
    return JSON.parse(request.body).query.includes('RefreshSession');
}

function createDeferred() {
    let resolve;
    const promise = new Promise((next) => {
        resolve = next;
    });
    return { promise, resolve };
}

afterEach(() => {
    clearAuthSession();
    setAuthFailureHandler();
    vi.unstubAllGlobals();
});

describe('authenticated GraphQL session refresh', () => {
    it('refreshes before the access token expires and then sends the original request', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn(10) });
        const freshToken = tokenExpiringIn(900);
        const fetchImpl = vi.fn((_, request) => {
            if (isRefreshRequest(request)) {
                return jsonResponse({
                    data: {
                        refreshSession: {
                            email: 'user@example.com',
                            token: freshToken,
                            accessToken: freshToken,
                        },
                    },
                });
            }
            return jsonResponse({ data: { me: { email: 'user@example.com' } } });
        });

        const data = await requestAuthenticated(QUERY, undefined, fetchImpl);

        expect(data.me.email).toBe('user@example.com');
        expect(getAccessToken()).toBe(freshToken);
        expect(fetchImpl).toHaveBeenCalledTimes(2);
        expect(isRefreshRequest(fetchImpl.mock.calls[0][1])).toBe(true);
    });

    it('shares one refresh request across simultaneous protected requests', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn(10) });
        const refresh = createDeferred();
        const fetchImpl = vi.fn((_, request) => {
            if (isRefreshRequest(request)) return refresh.promise;
            return jsonResponse({ data: { me: { email: 'user@example.com' } } });
        });

        const first = requestAuthenticated(QUERY, undefined, fetchImpl);
        const second = requestAuthenticated(QUERY, undefined, fetchImpl);
        refresh.resolve(jsonResponse({
            data: {
                refreshSession: {
                    email: 'user@example.com',
                    token: tokenExpiringIn(900),
                    accessToken: tokenExpiringIn(900),
                },
            },
        }));

        await Promise.all([first, second]);

        const refreshRequests = fetchImpl.mock.calls.filter(([, request]) => (
            isRefreshRequest(request)
        ));
        expect(refreshRequests).toHaveLength(1);
        expect(fetchImpl).toHaveBeenCalledTimes(3);
    });

    it('refreshes on a 401 and retries the original request once', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn(900) });
        const fetchImpl = vi
            .fn()
            .mockImplementationOnce(() => jsonResponse({
                errors: [{ message: 'Token expired' }],
            }, 401))
            .mockImplementationOnce(() => jsonResponse({
                data: {
                    refreshSession: {
                        email: 'user@example.com',
                        token: tokenExpiringIn(900),
                        accessToken: tokenExpiringIn(900),
                    },
                },
            }))
            .mockImplementationOnce(() => jsonResponse({
                data: { me: { email: 'user@example.com' } },
            }));

        const data = await requestAuthenticated(QUERY, undefined, fetchImpl);

        expect(data.me.email).toBe('user@example.com');
        expect(fetchImpl).toHaveBeenCalledTimes(3);
        expect(isRefreshRequest(fetchImpl.mock.calls[1][1])).toBe(true);
    });

    it('clears the session and runs the auth failure handler when refresh fails', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn(10) });
        const onAuthFailure = vi.fn();
        setAuthFailureHandler(onAuthFailure);
        const fetchImpl = vi.fn(() => jsonResponse({
            errors: [{ message: 'Invalid CSRF token' }],
        }, 401));

        await expect(requestAuthenticated(QUERY, undefined, fetchImpl)).rejects.toThrow();

        expect(isAuthenticated.value).toBe(false);
        expect(getAccessToken()).toBeNull();
        expect(onAuthFailure).toHaveBeenCalledTimes(1);
    });
});
