# Notifications

The app has two independent notification systems that share the same
underlying data: **in-app notifications** (bell panel + live toast stack) and
**browser push notifications** (native OS popups, delivered even when the app
tab/window is closed).

Every notification is a `SystemNotification` row. Browser push is just an
extra delivery channel layered on top of that same row — creating a
notification through any path (task reminders, a manual `createSystemNotification`
mutation, or future notification sources) triggers both.

## 1. In-App Notifications

### Priority

Each notification has a `priority` of `info`, `warning`, or `danger`,
independent from the older cosmetic `color` field. The topbar bell panel and
toast stack use `priority` to pick an icon and accent color.

### Task Reminders

A background sweep (started in `main.py`'s FastAPI `lifespan`, alongside the
existing stale-session sweeper) periodically scans `SystemTask` rows for
`date_assign` (start) and `date_due` (due) times and generates reminder
notifications automatically — no manual trigger needed.

```env
TASK_REMINDER_EARLY_MINUTES=30
TASK_REMINDER_FINAL_MINUTES=5
TASK_REMINDER_SWEEP_INTERVAL_SECONDS=60
```

- `TASK_REMINDER_EARLY_MINUTES`: first reminder, fired this many minutes before the event.
- `TASK_REMINDER_FINAL_MINUTES`: final, more urgent reminder.
- `TASK_REMINDER_SWEEP_INTERVAL_SECONDS`: how often the sweep runs.

Priority is assigned automatically by urgency:

| Event                        | Priority  |
| ----------------------------- | --------- |
| Task starting (early warning) | `info`    |
| Task due (early warning)      | `warning` |
| Task starting (final, 5 min)  | `danger`  |
| Task due (final, 5 min)       | `danger`  |

Each reminder is deduplicated via a `dedupe_key` column
(`task_reminder:<task_uuid>:<start_early|start_final|due_early|due_final>`),
so re-running the sweep never creates duplicates for the same task/event.

### GraphQL

```graphql
query SystemMyNotifications($limit: Int!) {
  systemMyNotifications(limit: $limit) {
    uuid
    date
    priority
    status
    title
    message
    read
  }
}

mutation MarkRead($uuid: UUID!) {
  updateSystemNotification(notificationUuid: $uuid, notification: { read: true, status: read }) {
    uuid
  }
}

query SystemPendingCounts {
  systemPendingCounts { messages notifications }
}
```

`systemMyNotifications` is scoped to the current user (direct `user_id` target
or member of the multi-user `users` list). `systemNotifications` (no `My`)
returns every notification and is meant for admin/back-office use.

### Frontend

- **Bell + badge** (`topbar.jsx`): polls `systemPendingCounts` (interval set
  by `VITE_PENDING_COUNTS_INTERVAL_MS`, default 60s) and shows the unread
  count.
- **Dropdown panel**: opens on bell click, lists the user's recent
  notifications (read and unread) via `systemMyNotifications`. Clicking an
  unread item marks it read.
- **Live toast stack** (`AlertStack.jsx`, mounted once outside `#app` so it
  survives route changes): notifications are polled separately (interval set
  by `VITE_NOTIFICATIONS_POLL_INTERVAL_MS`, default 30s, see
  `notificationsStore.js`). Only notifications whose `date` is **after** the
  current tab's session start show up as a toast — anything generated while
  the tab was closed only appears in the bell panel, never as a toast replay.
  Toasts never auto-dismiss; the user must close each one explicitly. New
  toasts enter bottom-right and push earlier ones upward.

## 2. Browser Push Notifications

Delivers a native OS-level popup through the browser's Push API, so the user
sees it even with the app tab/window fully closed.

### Requirements

- A VAPID key pair (identifies this server to the push service).
- HTTPS in production (browsers only allow the Push API on secure origins;
  `localhost` is exempted for development).
- A **non-incognito** browser profile. Chrome deliberately disables the Push
  API in incognito/private/automation-default contexts — this matters if you
  ever script this flow (e.g. with Playwright), not for real users.

### Configuration

```env
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@example.com
```

Generate a pair with:

```bash
python -m app.core.push.generate_vapid_keys
```

Copy the printed `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` into `.env`.
`VAPID_SUBJECT` is a contact URI/mailto the push service can use to reach you
if it needs to (per the Web Push VAPID spec). If either key is missing, push
sending is skipped silently — in-app notifications keep working normally.

### GraphQL

```graphql
query SystemPushPublicKey {
  systemPushPublicKey
}

mutation Subscribe($subscription: SystemPushSubscriptionInput!) {
  saveSystemPushSubscription(subscription: $subscription)
}

mutation Unsubscribe($endpoint: String!) {
  deleteSystemPushSubscription(endpoint: $endpoint)
}
```

Subscriptions are stored in `system_push_subscriptions` (`endpoint`, `p256dh`,
`auth`, `user_id`). An endpoint is unique — subscribing again from the same
browser/device upserts the existing row instead of duplicating it.

### How delivery works

`SystemNotificationService.create()` calls `WebPushService.send_to_user()`
for every recipient after the notification row is committed. It:

1. Loads that user's subscriptions.
2. Sends an encrypted Web Push payload (`{title, body, url}`) to each via
   `pywebpush`, signed with the VAPID private key.
3. If a push service responds `404`/`410` (subscription no longer exists on
   the browser/OS side), the subscription row is deleted automatically.
4. Any other failure is logged and swallowed — a push failure never blocks or
   rolls back the notification itself.

### Frontend

- **`public/sw.js`**: the service worker. Its `push` handler shows the native
  notification (`registration.showNotification`) and — if a tab is still
  open — `postMessage`s the payload back to it so the in-app toast stack can
  refresh immediately instead of waiting for its next poll. Its
  `notificationclick` handler focuses an existing tab or opens a new one.
- **`app/api/webPush.js`**: `registerServiceWorker()`, `enableWebPush()`
  (requests permission, subscribes, saves to the backend),
  `disableWebPush()`, `getWebPushStatus()`.
- **UI**: an "Enable browser notifications" / "Disable browser notifications"
  toggle in the bell dropdown's header, shown only when the browser supports
  the Push API. It shows "Browser notifications are blocked" instead if the
  user previously denied the permission.

## Adding A New Notification Source

To make some other event (not a task reminder) show up in both channels,
build the notification data (`title`/`message` as `{es, en}` dicts, `priority`,
`user_id` or `user_uuid`) and call
`SystemNotificationService.create(...)` — both the in-app and push paths are
wired at that single entry point.
