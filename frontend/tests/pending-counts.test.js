import { afterEach, describe, expect, it, vi } from 'vitest';

import {
    fetchPendingCounts,
    refreshPendingCounts,
    startPendingCountsPolling,
    stopPendingCountsPolling,
} from '../src/app/api/pendingCounts.js';
import { appSignal } from '../src/app/store/appStore.js';
import { clearAuthSession, setAuthSession } from '../src/app/store/authStore.js';

function tokenExpiringIn(seconds = 900) {
    const payload = globalThis.btoa(JSON.stringify({
        exp: Math.floor(Date.now() / 1000) + seconds,
    }));
    return `header.${payload}.signature`;
}

function jsonResponse(body) {
    return Promise.resolve(
        new Response(JSON.stringify(body), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
        }),
    );
}

function pendingCountsResponse(messages = 3, notifications = 5) {
    return jsonResponse({
        data: {
            systemPendingCounts: { messages, notifications },
        },
    });
}

function setVisibility(value) {
    Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        value,
    });
}

function createDeferred() {
    let resolve;
    const promise = new Promise((next) => {
        resolve = next;
    });
    return { promise, resolve };
}

afterEach(() => {
    vi.useRealTimers();
    stopPendingCountsPolling();
    clearAuthSession();
    setVisibility('visible');
});

describe('fetchPendingCounts', () => {
    it('requests unread message and notification counts', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const fetchImpl = async (_url, request) => {
            expect(JSON.parse(request.body).query).toContain('systemPendingCounts');
            return pendingCountsResponse();
        };

        await expect(fetchPendingCounts(fetchImpl)).resolves.toEqual({
            messages: 3,
            notifications: 5,
        });
    });

    it('refreshes immediately and then every 60 seconds while visible', async () => {
        vi.useFakeTimers();
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const fetchImpl = vi.fn(() => pendingCountsResponse(2, 7));

        startPendingCountsPolling(fetchImpl);
        await Promise.resolve();
        await Promise.resolve();

        expect(fetchImpl).toHaveBeenCalledTimes(1);
        await vi.waitFor(() => {
            expect(appSignal.value.pendingCounts).toEqual({ messages: 2, notifications: 7 });
        });

        await vi.advanceTimersByTimeAsync(60_000);

        expect(fetchImpl).toHaveBeenCalledTimes(2);
    });

    it('does not refresh while hidden and refreshes when visible again', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        setVisibility('hidden');
        const fetchImpl = vi.fn(() => pendingCountsResponse());

        await refreshPendingCounts(fetchImpl);

        expect(fetchImpl).not.toHaveBeenCalled();

        setVisibility('visible');
        await refreshPendingCounts(fetchImpl);

        expect(fetchImpl).toHaveBeenCalledTimes(1);
    });

    it('shares a pending counts request already in flight', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const pending = createDeferred();
        const fetchImpl = vi.fn(() => pending.promise);

        const first = refreshPendingCounts(fetchImpl);
        const second = refreshPendingCounts(fetchImpl);
        pending.resolve(pendingCountsResponse(1, 2));

        await Promise.all([first, second]);

        expect(fetchImpl).toHaveBeenCalledTimes(1);
        expect(appSignal.value.pendingCounts).toEqual({ messages: 1, notifications: 2 });
    });
});
