import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const INTERNAL_MESSAGE_RECIPIENTS = gql`
  query InternalMessageRecipients($model: String!, $use: SystemModelSchemaUse!, $name: String!) {
    systemModelView(model: $model, use: $use, name: $name) {
      records
    }
  }
`;

const CREATE_INTERNAL_MESSAGE = gql`
  mutation CreateInternalMessage($message: SystemMessageCreateInput!) {
    createSystemMessage(message: $message) {
      uuid
      status
      date
      subject
      message
      fromUser { uuid name email }
      toUsers { uuid name email }
      createdAt
    }
  }
`;

export async function createInternalMessage(
    { subject, html, senderUuid, recipientUuids, lang = 'en' },
    fetchImpl = globalThis.fetch,
) {
    const data = await requestAuthenticated(CREATE_INTERNAL_MESSAGE, {
        message: {
            subject: { [lang]: subject },
            message: { [lang]: html },
            fromUserUuid: senderUuid,
            toUserUuids: recipientUuids,
        },
    }, fetchImpl);
    return data.createSystemMessage;
}

export async function listInternalMessageRecipients(fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        INTERNAL_MESSAGE_RECIPIENTS,
        { model: 'user.user', use: 'view', name: 'default' },
        fetchImpl,
    );
    return data.systemModelView?.records ?? [];
}
