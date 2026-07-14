import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';
import { isAuthenticated } from '../store/authStore.js';
import { dashboardActions } from '../store/actions';

const PENDING_COUNTS_INTERVAL_MS = Number(
    import.meta.env.VITE_PENDING_COUNTS_INTERVAL_MS ?? 60_000,
);

const PENDING_COUNTS_QUERY = gql`
  query SystemPendingCounts {
    systemPendingCounts {
      messages
      notifications
    }
  }
`;

export async function fetchPendingCounts(fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        PENDING_COUNTS_QUERY,
        undefined,
        fetchImpl,
    );
    return data.systemPendingCounts;
}

let pendingCountsTimer = null;
let pendingCountsInFlight = null;

function isVisible() {
    return !globalThis.document || globalThis.document.visibilityState !== 'hidden';
}

export async function refreshPendingCounts(fetchImpl = globalThis.fetch) {
    if (!isAuthenticated.value || !isVisible()) return null;
    if (!pendingCountsInFlight) {
        pendingCountsInFlight = fetchPendingCounts(fetchImpl)
            .then((counts) => {
                dashboardActions.setPendingCounts(counts);
                return counts;
            })
            .catch((error) => {
                dashboardActions.setPendingCounts({ messages: 0, notifications: 0 });
                throw error;
            })
            .finally(() => {
                pendingCountsInFlight = null;
            });
    }
    return pendingCountsInFlight;
}

function onVisibilityChange() {
    if (isVisible()) {
        void refreshPendingCounts().catch(() => {});
    }
}

export function startPendingCountsPolling(fetchImpl = globalThis.fetch) {
    if (pendingCountsTimer || !isAuthenticated.value) return;
    void refreshPendingCounts(fetchImpl).catch(() => {});
    pendingCountsTimer = globalThis.setInterval(() => {
        void refreshPendingCounts(fetchImpl).catch(() => {});
    }, PENDING_COUNTS_INTERVAL_MS);
    globalThis.document?.addEventListener?.('visibilitychange', onVisibilityChange);
}

export function stopPendingCountsPolling() {
    if (pendingCountsTimer) {
        globalThis.clearInterval(pendingCountsTimer);
        pendingCountsTimer = null;
    }
    pendingCountsInFlight = null;
    globalThis.document?.removeEventListener?.('visibilitychange', onVisibilityChange);
}
