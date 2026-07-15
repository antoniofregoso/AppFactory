import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/app/api/session.js', () => ({ requestAuthenticated: vi.fn() }));

import { createNote, deleteNote, listNotes } from '../src/app/api/notes.js';
import { requestAuthenticated } from '../src/app/api/session.js';

afterEach(() => requestAuthenticated.mockReset());

describe('notes GraphQL API', () => {
    it('lists and normalizes notes', async () => {
        requestAuthenticated.mockResolvedValue({ systemNotes: [{
            uuid: 'note-1', modelUuid: 'model-1', recordUuid: 'record-1',
            contentHtml: '<p>Nota</p>', authorUuid: 'user-1', authorName: 'Ana', createdAt: 'now',
        }] });
        const [note] = await listNotes({ modelUuid: 'model-1', recordUuid: 'record-1' });
        expect(note).toMatchObject({ uuid: 'note-1', content_html: '<p>Nota</p>', author_name: 'Ana' });
    });

    it('creates a note', async () => {
        requestAuthenticated.mockResolvedValue({ createSystemNote: {
            uuid: 'note-1', modelUuid: 'model-1', recordUuid: 'record-1',
            contentHtml: '<p>Nota</p>', authorUuid: null, authorName: null, createdAt: 'now',
        } });
        const note = await createNote({ modelUuid: 'model-1', recordUuid: 'record-1', contentHtml: '<p>Nota</p>' });
        expect(note.content_html).toBe('<p>Nota</p>');
        expect(requestAuthenticated.mock.calls[0][1].note).toEqual({
            modelUuid: 'model-1', recordUuid: 'record-1', contentHtml: '<p>Nota</p>',
        });
    });

    it('deletes a note', async () => {
        requestAuthenticated.mockResolvedValue({ deleteSystemNote: true });
        await deleteNote('note-1');
        expect(requestAuthenticated.mock.calls[0][1]).toEqual({ noteUuid: 'note-1' });
    });
});
