import { signal } from '@preact/signals';

import { fetchMyNotifications } from '../api/notifications.js';
import { isAuthenticated } from './authStore.js';

const POLL_INTERVAL_MS = Number(
    import.meta.env.VITE_NOTIFICATIONS_POLL_INTERVAL_MS ?? 30_000,
);

// Recent notifications for the current user (bell dropdown panel).
export const notificationsSignal = signal([]);
// Notifications observed for the first time since this tab/session was opened —
// consumed by the animated toast stack. Reminders that fired while the user
// was offline stay out of this queue; they only ever show up in the panel.
export const newAlertsSignal = signal([]);

const sessionStartAt = Date.now();
const seenUuids = new Set();
let pollTimer = null;
let inFlight = null;

function isVisible() {
    return !globalThis.document || globalThis.document.visibilityState !== 'hidden';
}

async function refresh(fetchImpl = globalThis.fetch) {
    if (!isAuthenticated.value || !isVisible()) return null;
    if (inFlight) return inFlight;

    inFlight = fetchMyNotifications(30, fetchImpl)
        .then((notifications) => {
            notificationsSignal.value = notifications;

            const arrivals = notifications.filter((notification) => {
                if (seenUuids.has(notification.uuid)) return false;
                seenUuids.add(notification.uuid);
                const occurredAt = new Date(notification.date).getTime();
                return Number.isFinite(occurredAt) && occurredAt >= sessionStartAt;
            });
            if (arrivals.length) {
                newAlertsSignal.value = [...newAlertsSignal.value, ...arrivals];
            }
            return notifications;
        })
        .catch((error) => {
            console.error('Unable to refresh notifications.', error);
        })
        .finally(() => {
            inFlight = null;
        });
    return inFlight;
}

function onVisibilityChange() {
    if (isVisible()) void refresh();
}

function onServiceWorkerMessage(event) {
    if (event.data?.type === 'push-notification') void refresh();
}

export function startNotificationsPolling(fetchImpl = globalThis.fetch) {
    if (pollTimer || !isAuthenticated.value) return;
    void refresh(fetchImpl);
    pollTimer = globalThis.setInterval(() => void refresh(fetchImpl), POLL_INTERVAL_MS);
    globalThis.document?.addEventListener?.('visibilitychange', onVisibilityChange);
    globalThis.navigator?.serviceWorker?.addEventListener?.('message', onServiceWorkerMessage);
}

export function stopNotificationsPolling() {
    if (pollTimer) {
        globalThis.clearInterval(pollTimer);
        pollTimer = null;
    }
    inFlight = null;
    seenUuids.clear();
    notificationsSignal.value = [];
    newAlertsSignal.value = [];
    globalThis.document?.removeEventListener?.('visibilitychange', onVisibilityChange);
    globalThis.navigator?.serviceWorker?.removeEventListener?.('message', onServiceWorkerMessage);
}

export function refreshNotificationsNow(fetchImpl = globalThis.fetch) {
    return refresh(fetchImpl);
}

export function markNotificationReadLocally(notificationUuid) {
    notificationsSignal.value = notificationsSignal.value.map((notification) => (
        notification.uuid === notificationUuid
            ? { ...notification, read: true }
            : notification
    ));
}
