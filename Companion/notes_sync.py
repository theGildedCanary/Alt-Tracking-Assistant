"""Bidirectional addon Notes / History entries, independent of HTML character info."""
import copy
import time
import uuid
import db
import settings_sync

STATE_KEY = 'character_history'
DELETED_KEY = 'character_history_deleted'

def entries(value):
    return list(value.values()) if isinstance(value, dict) else list(value or [])

def load(conn):
    return db.get_json(conn, STATE_KEY) or {}

def merge(conn, records):
    state = load(conn)
    deleted = db.get_json(conn, DELETED_KEY) or {}
    for record in records:
        guid = record.get('guid')
        if not guid or 'notes' not in record and 'notesDeleted' not in record:
            continue
        notes = state.setdefault(guid, [])
        tombstones = deleted.setdefault(guid, {})
        for ident, stamp in (record.get('notesDeleted') or {}).items():
            tombstones[ident] = max(tombstones.get(ident, 0), stamp)
        for incoming in entries(record.get('notes')):
            note = copy.deepcopy(incoming)
            ident = note.get('id')
            if not ident or tombstones.get(ident, 0) >= note.get('changedAt', note.get('created', 0)):
                continue
            old = next((item for item in notes if item['id'] == ident), None)
            if old is None:
                notes.append(note)
            elif note.get('changedAt', note.get('created', 0)) > old.get('changedAt', old.get('created', 0)):
                old.update(note)
        notes[:] = [note for note in notes if tombstones.get(note['id'], 0) < note.get('changedAt', note.get('created', 0))]
    db.set_json(conn, STATE_KEY, state)
    db.set_json(conn, DELETED_KEY, deleted)
    return state

def save(conn, paths, guid, note_id, text=None):
    state = load(conn)
    notes = state.setdefault(guid, [])
    deleted = db.get_json(conn, DELETED_KEY) or {}
    now = time.time()
    if text is None:
        deleted.setdefault(guid, {})[note_id] = now
        notes[:] = [item for item in notes if item['id'] != note_id]
    else:
        text = text.strip()
        if not text:
            raise ValueError('Enter a note first.')
        if len(text.encode('utf-8')) > 1000:
            raise ValueError('Notes are limited to 1,000 UTF-8 bytes, matching the addon.')
        note = next((item for item in notes if item['id'] == note_id), None)
        if note is None:
            note = {'id': uuid.uuid4().hex, 'created': int(now)}
            notes.append(note)
        note.update(text=text, changedAt=now)
    db.set_json(conn, STATE_KEY, state)
    db.set_json(conn, DELETED_KEY, deleted)
    return publish(conn, paths)

def publish(conn, paths):
    state = load(conn)
    deleted = db.get_json(conn, DELETED_KEY) or {}
    payload = {guid: {'notes': state.get(guid, []), 'deleted': deleted.get(guid, {})}
               for guid in set(state) | set(deleted)}
    source = '-- Companion Notes / History edits.\nAltTrackingAssistantNotesSync = ' + settings_sync._lua_value(payload) + '\n'
    folders = settings_sync.addon_dirs(paths)
    for folder in folders:
        target = folder / 'NotesSync.lua'
        if not target.exists() or target.read_text(encoding='utf-8') != source:
            target.write_text(source, encoding='utf-8')
    return len(folders)
