import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';
import { isAuthenticated } from '../store/authStore.js';

const MY_NOTIFICATIONS_QUERY = gql`
  query SystemMyNotifications($limit: Int!) {
    systemMyNotifications(limit: $limit) {
      uuid
      date
      status
      title
      message
      read
      priority
      createdAt
    }
  }
`;

const MARK_NOTIFICATION_READ_MUTATION = gql`
  mutation MarkSystemNotificationRead($notificationUuid: UUID!) {
    updateSystemNotification(
      notificationUuid: $notificationUuid
      notification: { read: true, status: read }
    ) {
      uuid
      read
      status
    }
  }
`;

export async function fetchMyNotifications(limit = 30, fetchImpl = globalThis.fetch) {
    if (!isAuthenticated.value) return [];
    const data = await requestAuthenticated(
        MY_NOTIFICATIONS_QUERY,
        { limit },
        fetchImpl,
    );
    return data.systemMyNotifications ?? [];
}

export async function markNotificationRead(notificationUuid, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        MARK_NOTIFICATION_READ_MUTATION,
        { notificationUuid },
        fetchImpl,
    );
    return data.updateSystemNotification;
}
