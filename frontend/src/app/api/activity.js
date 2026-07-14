import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';
import { isAuthenticated } from '../store/authStore.js';

const HEARTBEAT_INTERVAL_MS = Number(
    import.meta.env.VITE_USER_HEARTBEAT_INTERVAL_MS ?? 45_000,
);

const HEARTBEAT_MUTATION = gql`
  mutation Heartbeat {
    heartbeat {
      uuid
      status
      lastSeenAt
    }
  }
`;

let heartbeatTimer = null;
let heartbeatInFlight = null;

function isVisible() {
    return !globalThis.document || globalThis.document.visibilityState !== 'hidden';
}

export async function sendHeartbeat(fetchImpl = globalThis.fetch) {
    if (!isAuthenticated.value || !isVisible()) return null;
    if (!heartbeatInFlight) {
        heartbeatInFlight = requestAuthenticated(
            HEARTBEAT_MUTATION,
            undefined,
            fetchImpl,
        ).finally(() => {
            heartbeatInFlight = null;
        });
    }
    return heartbeatInFlight;
}

function onVisibilityChange() {
    if (isVisible()) {
        void sendHeartbeat().catch(() => {});
    }
}

export function startActivityHeartbeat(fetchImpl = globalThis.fetch) {
    if (heartbeatTimer || !isAuthenticated.value) return;
    void sendHeartbeat(fetchImpl).catch(() => {});
    heartbeatTimer = globalThis.setInterval(() => {
        void sendHeartbeat(fetchImpl).catch(() => {});
    }, HEARTBEAT_INTERVAL_MS);
    globalThis.document?.addEventListener?.('visibilitychange', onVisibilityChange);
}

export function stopActivityHeartbeat() {
    if (heartbeatTimer) {
        globalThis.clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
    heartbeatInFlight = null;
    globalThis.document?.removeEventListener?.('visibilitychange', onVisibilityChange);
}
