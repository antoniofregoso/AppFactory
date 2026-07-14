import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({ requestAuthenticated: vi.fn() }));

import { createInternalMessage, listInternalMessageRecipients } from '../src/app/api/messages.js';
import { requestAuthenticated } from '../src/app/api/session.js';

afterEach(() => requestAuthenticated.mockReset());

describe('internal messages API', () => {
  it('loads recipient users independently from follower options', async () => {
    const records = [{ uuid: 'user-2', name: 'Laslo', active: true, user_type: 'HUMAN' }];
    requestAuthenticated.mockResolvedValue({ systemModelView: { records } });
    await expect(listInternalMessageRecipients()).resolves.toEqual(records);
    expect(requestAuthenticated).toHaveBeenCalledWith(
      expect.stringContaining('systemModelView(model: $model'),
      { model: 'user.user', use: 'view', name: 'default' }, expect.any(Function),
    );
  });
  it('creates a message with sender and recipients', async () => {
    requestAuthenticated.mockResolvedValue({ createSystemMessage: { uuid: 'message-1' } });
    await expect(createInternalMessage({
      subject: 'Hola', html: '<p>Mensaje</p>', senderUuid: 'user-1', recipientUuids: ['user-2'], lang: 'es',
    })).resolves.toEqual({ uuid: 'message-1' });
    expect(requestAuthenticated).toHaveBeenCalledWith(
      expect.stringContaining('createSystemMessage'),
      { message: {
        subject: { es: 'Hola' }, message: { es: '<p>Mensaje</p>' },
        fromUserUuid: 'user-1', toUserUuids: ['user-2'],
      } },
      expect.any(Function),
    );
  });
});
