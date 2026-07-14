// Minimal service worker: only handles push delivery and notification
// clicks. No offline caching — this app is not a full PWA (yet).

self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    let payload = { title: 'Dashboard', body: '', url: '/dashboard' };
    try {
        if (event.data) payload = { ...payload, ...event.data.json() };
    } catch {
        // Non-JSON push payload — fall back to the defaults above.
    }

    event.waitUntil(
        Promise.all([
            self.registration.showNotification(payload.title, {
                body: payload.body,
                icon: '/logo.png',
                badge: '/favicon.svg',
                data: { url: payload.url },
            }),
            // Let any open tab refresh immediately instead of waiting for its
            // next poll cycle — same notification, shown twice as fast.
            self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
                clients.forEach((client) => client.postMessage({ type: 'push-notification', payload }));
            }),
        ]),
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = event.notification.data?.url ?? '/dashboard';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
            const existing = clients.find((client) => 'focus' in client);
            if (existing) {
                existing.navigate(targetUrl);
                return existing.focus();
            }
            return self.clients.openWindow(targetUrl);
        }),
    );
});
