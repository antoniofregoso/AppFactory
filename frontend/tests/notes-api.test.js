import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({ requestAuthenticatedFetch: vi.fn() }));

import { createNote, deleteNote, listNotes } from '../src/app/api/notes.js';
import { requestAuthenticatedFetch } from '../src/app/api/session.js';

afterEach(() => requestAuthenticatedFetch.mockReset());

describe('notes API', () => {
  it('lists notes for a record', async () => {
    const notes = [{ uuid: 'note-1' }];
    requestAuthenticatedFetch.mockResolvedValue({ ok: true, json: vi.fn().mockResolvedValue(notes) });
    await expect(listNotes({ modelUuid: 'model-1', recordUuid: 'record-1' })).resolves.toEqual(notes);
    expect(requestAuthenticatedFetch).toHaveBeenCalledWith('/api/system/notes/record/model-1/record-1', {}, expect.any(Function));
  });

  it('creates a note for a record', async () => {
    const note = { uuid: 'note-1', content_html: '<p>Nota</p>' };
    requestAuthenticatedFetch.mockResolvedValue({ ok: true, json: vi.fn().mockResolvedValue(note) });
    await expect(createNote({ modelUuid: 'model-1', recordUuid: 'record-1', contentHtml: '<p>Nota</p>' })).resolves.toEqual(note);
    expect(requestAuthenticatedFetch).toHaveBeenCalledWith('/api/system/notes', expect.objectContaining({
      method: 'POST', body: JSON.stringify({ model_uuid: 'model-1', record_uuid: 'record-1', content_html: '<p>Nota</p>' }),
    }), expect.any(Function));
  });

  it('deletes a note', async () => {
    requestAuthenticatedFetch.mockResolvedValue({ ok: true });
    await expect(deleteNote('note-1')).resolves.toBeUndefined();
    expect(requestAuthenticatedFetch).toHaveBeenCalledWith('/api/system/notes/note-1', { method: 'DELETE' }, expect.any(Function));
  });
});
