import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({ requestAuthenticated: vi.fn() }));

import { createSystemModelRecord } from '../src/app/api/systemModel.js';
import { requestAuthenticated } from '../src/app/api/session.js';

afterEach(() => requestAuthenticated.mockReset());

describe('createSystemModelRecord', () => {
  it('returns the record created by GraphQL', async () => {
    const record = { uuid: 'user-2', name: 'Ana Admin' };
    requestAuthenticated.mockResolvedValue({ createSystemModelRecord: record });
    await expect(createSystemModelRecord({ model: 'user.user', values: { name: 'Ana Admin' } })).resolves.toEqual(record);
    expect(requestAuthenticated).toHaveBeenCalledWith(
      expect.stringContaining('createSystemModelRecord'),
      { model: 'user.user', values: { name: 'Ana Admin' } },
      expect.any(Function),
    );
  });
});
