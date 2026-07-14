import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const VAPID_PUBLIC_KEY_QUERY = gql`
  query SystemPushPublicKey {
    systemPushPublicKey
  }
`;

const SAVE_SUBSCRIPTION_MUTATION = gql`
  mutation SaveSystemPushSubscription($subscription: SystemPushSubscriptionInput!) {
    saveSystemPushSubscription(subscription: $subscription)
  }
`;

const DELETE_SUBSCRIPTION_MUTATION = gql`
  mutation DeleteSystemPushSubscription($endpoint: String!) {
    deleteSystemPushSubscription(endpoint: $endpoint)
  }
`;

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = globalThis.atob(base64);
    return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

export function isWebPushSupported() {
    return Boolean(
        globalThis.navigator?.serviceWorker
        && globalThis.window?.PushManager
        && globalThis.window?.Notification,
    );
}

export async function registerServiceWorker() {
    if (!isWebPushSupported()) return null;
    return navigator.serviceWorker.register('/sw.js');
}

export async function getExistingPushSubscription() {
    if (!isWebPushSupported()) return null;
    const registration = await navigator.serviceWorker.ready;
    return registration.pushManager.getSubscription();
}

/** 'unsupported' | 'denied' | 'default' | 'subscribed' | 'not-subscribed' */
export async function getWebPushStatus() {
    if (!isWebPushSupported()) return 'unsupported';
    if (Notification.permission === 'denied') return 'denied';
    if (Notification.permission === 'default') return 'default';
    const subscription = await getExistingPushSubscription();
    return subscription ? 'subscribed' : 'not-subscribed';
}

export async function enableWebPush(fetchImpl = globalThis.fetch) {
    if (!isWebPushSupported()) throw new Error('Web push is not supported in this browser.');

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Notification permission was not granted.');

    const registration = await registerServiceWorker();
    const { systemPushPublicKey } = await requestAuthenticated(VAPID_PUBLIC_KEY_QUERY, undefined, fetchImpl);
    if (!systemPushPublicKey) throw new Error('The server has no VAPID public key configured.');

    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(systemPushPublicKey),
        });
    }

    const json = subscription.toJSON();
    await requestAuthenticated(SAVE_SUBSCRIPTION_MUTATION, {
        subscription: {
            endpoint: json.endpoint,
            p256dh: json.keys.p256dh,
            auth: json.keys.auth,
            userAgent: navigator.userAgent,
        },
    }, fetchImpl);

    return subscription;
}

export async function disableWebPush(fetchImpl = globalThis.fetch) {
    const subscription = await getExistingPushSubscription();
    if (!subscription) return;

    const endpoint = subscription.endpoint;
    await subscription.unsubscribe();
    await requestAuthenticated(DELETE_SUBSCRIPTION_MUTATION, { endpoint }, fetchImpl);
}
