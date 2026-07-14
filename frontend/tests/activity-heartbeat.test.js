import { afterEach, describe, expect, it, vi } from 'vitest';

import {
    sendHeartbeat,
    startActivityHeartbeat,
    stopActivityHeartbeat,
} from '../src/app/api/activity.js';
import { clearAuthSession, setAuthSession } from '../src/app/store/authStore.js';

function tokenExpiringIn(seconds = 900) {
    const payload = globalThis.btoa(JSON.stringify({
        exp: Math.floor(Date.now() / 1000) + seconds,
    }));
    return `header.${payload}.signature`;
}

function heartbeatResponse() {
    return Promise.resolve(
        new Response(JSON.stringify({
            data: {
                heartbeat: {
                    uuid: '11111111-0000-4000-8000-000000000000',
                    status: 'ONLINE',
                    lastSeenAt: new Date().toISOString(),
                },
            },
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
        }),
    );
}

function setVisibility(value) {
    Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        value,
    });
}

afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    stopActivityHeartbeat();
    clearAuthSession();
    setVisibility('visible');
});

describe('activity heartbeat', () => {
    it('sends an authenticated heartbeat immediately and on the interval', async () => {
        vi.useFakeTimers();
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const fetchImpl = vi.fn(() => heartbeatResponse());

        startActivityHeartbeat(fetchImpl);
        await Promise.resolve();
        await Promise.resolve();

        expect(fetchImpl).toHaveBeenCalledTimes(1);
        expect(JSON.parse(fetchImpl.mock.calls[0][1].body).query).toContain(
            'heartbeat',
        );

        await vi.advanceTimersByTimeAsync(45_000);

        expect(fetchImpl).toHaveBeenCalledTimes(2);
    });

    it('does not ping while the tab is hidden', async () => {
        setVisibility('hidden');
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const fetchImpl = vi.fn(() => heartbeatResponse());

        await sendHeartbeat(fetchImpl);

        expect(fetchImpl).not.toHaveBeenCalled();
    });

    it('reuses the heartbeat request already in flight', async () => {
        setAuthSession({ email: 'user@example.com', token: tokenExpiringIn() });
        const fetchImpl = vi.fn(() => heartbeatResponse());

        await Promise.all([
            sendHeartbeat(fetchImpl),
            sendHeartbeat(fetchImpl),
        ]);

        expect(fetchImpl).toHaveBeenCalledTimes(1);
    });
});
