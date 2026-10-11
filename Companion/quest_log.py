"""Persistent opt-in quest assignments and reset-aware manual tasks."""
import copy
import time
import uuid
from datetime import datetime, timedelta, timezone

import db
import settings_sync

STATE_KEY = "quest_log"
STATUSES = ("Pending", "In progress", "Completed")
RESETS = ("Unknown", "None", "Daily", "Weekly")
EST = timezone(timedelta(hours=-5), 'EST')


def next_reset(reset, now=None, reset_days=None):
    """User-defined resets: 11 a.m. fixed EST, Tuesday for weekly tasks."""
    if reset not in ('Daily', 'Weekly', 'Custom'):
        return None
    current = datetime.fromtimestamp(time.time() if now is None else now, EST)
    boundary = current.replace(hour=11, minute=0, second=0, microsecond=0)
    days = set(reset_days or [2]) if reset == 'Weekly' else set(reset_days or []) if reset == 'Custom' else set(range(1, 8))
    for offset in range(8):
        candidate = boundary + timedelta(days=offset)
        if candidate > current and candidate.isoweekday() in days:
            return candidate.timestamp()
    return None


def task_name(task, record):
    return task.get('title') or snapshot(task, record).get('title') or 'Unnamed quest'


def assignment_key(task):
    """Quest IDs identify quests; shared IDs link copies of a manual task."""
    for kind in ('quest', 'achievement', 'item'):
        if task.get(kind + 'ID'):
            return (kind, task[kind + 'ID'])
    return ('manual', task.get('sharedID') or task['id'])


def assigned_characters(state, task):
    key = assignment_key(task)
    return {guid for guid, tasks in state.items() if any(assignment_key(t) == key for t in tasks)}


def assign_characters(state, source, selected, now=None):
    """Keep existing character progress; start newly assigned manual tasks pending."""
    now = time.time() if now is None else now
    selected = set(selected)
    key = assignment_key(source)
    template = copy.deepcopy(source)
    if not source.get('questID'):
        template['sharedID'] = key[1]
    for guid, tasks in state.items():
        existing = [task for task in tasks if assignment_key(task) == key]
        if guid not in selected:
            tasks[:] = [task for task in tasks if assignment_key(task) != key]
        elif existing:
            if not source.get('questID'):
                for task in existing:
                    task['sharedID'] = key[1]
        else:
            added = copy.deepcopy(template)
            added.update(id=uuid.uuid4().hex, status='Pending', changedAt=now)
            added.pop('resetAt', None)
            added.pop('resetSchedule', None)
            tasks.append(added)


def load(conn):
    raw = db.get_json(conn, STATE_KEY)
    return copy.deepcopy(raw) if isinstance(raw, dict) else {}


def save(conn, paths, state):
    previous = load(conn)
    removed = db.get_json(conn, 'quest_log_deleted') or {}
    for guid, tasks in previous.items():
        kept = {t['id'] for t in state.get(guid, [])}
        for task in tasks:
            if task['id'] not in kept:
                removed.setdefault(guid, {})[task['id']] = time.time()
    db.set_json(conn, 'quest_log_deleted', removed)
    db.set_json(conn, STATE_KEY, state)
    return publish(paths, state, removed)


def publish(paths, state, removed=None):
    assignments = {guid: {str(task['questID']): True for task in tasks if task.get('questID')}
                   for guid, tasks in state.items()}
    for guid in set(state) | set(removed or {}):
        assignments.setdefault(guid, {}).update(_tasks=state.get(guid, []), _deleted=(removed or {}).get(guid, {}))
    content = "-- Companion quest assignments.\nAltTrackingAssistantQuestSync = " + settings_sync._lua_value(assignments) + "\n"
    folders = settings_sync.addon_dirs(paths)
    for folder in folders:
        target = folder / "QuestSync.lua"
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
    return len(folders)


def new_task(title, quest_id=None, reset=None, notes="", priority="Normal", reset_days=None):
    title = title.strip()
    if quest_id is not None:
        if isinstance(quest_id, bool) or not str(quest_id).isascii() or not str(quest_id).isdigit() or not 0 < int(quest_id) <= 2147483647:
            raise ValueError("Enter a positive numeric quest ID.")
        quest_id = int(quest_id)
    if not title and quest_id is None:
        raise ValueError("Enter a task title.")
    if reset_days is not None:
        reset_days = sorted(set(reset_days))
        reset = 'Daily' if len(reset_days) == 7 else 'Weekly' if len(reset_days) == 1 else 'Custom' if reset_days else 'None'
    reset = reset or ('Auto' if quest_id else 'None')
    task = dict(id=uuid.uuid4().hex, title=title, questID=quest_id, reset=reset,
                notes=notes.strip(), priority=priority, status="Pending", changedAt=time.time())
    if reset_days is not None:
        task['resetDays'] = reset_days
    if reset == 'Custom':
        days = sorted(set(reset_days or []))
        if not days or any(day not in range(1, 8) for day in days):
            raise ValueError('Select at least one reset day.')
        task['resetDays'] = days
    if quest_id:
        task['resetMode'] = reset
    return task


def snapshot(task, record):
    data = record.get("questLog") or {}
    for kind in ('quest', 'achievement', 'item'):
        if task.get(kind + 'ID'):
            return (data.get(kind + 's') or {}).get(str(task[kind + 'ID']), {})
    return {}


def task_reset(task, record):
    if task.get('questID') and task.get('resetMode') in ('None', 'Daily', 'Weekly', 'Custom'):
        return task['resetMode']
    return snapshot(task, record).get("reset", "Unknown") if task.get("questID") else task.get("reset", "None")


def reset_boundary(reset, record=None, now=None):
    return next_reset(reset, now)


def task_status(task, record, now=None):
    now = time.time() if now is None else now
    reset = task_reset(task, record)
    if is_automatic(task):
        data = snapshot(task, record)
        if not data:
            return "Awaiting scan"
        scanned = data.get('scannedAt') or (record.get('questLog') or {}).get('scannedAt')
        boundary = next_reset(reset, scanned, task.get('resetDays')) if scanned else None
        if boundary and now >= boundary:
            return "Awaiting new scan"
        status = data.get("status", "Awaiting scan")
        # Preserve the uncertainty of older snapshots until objectives are scanned.
        if status == 'Pending':
            return 'Not picked up'
        if status != 'Completed' and data.get('pickedUp') and data.get('started') is False and data.get('objectivesKnown', True):
            return 'Picked up'
        if status == 'In progress' and data.get('pickedUp') and 'started' not in data and not data.get('readyToTurnIn'):
            return 'Awaiting objective scan'
        return status
    status = task.get("status", "Pending")
    due = task.get("resetAt")
    return "Pending" if due and now >= due else status


def set_status(task, status, record, now=None):
    now = time.time() if now is None else now
    task.update(status=status, changedAt=now)
    reset = task_reset(task, record)
    task['resetAt'] = next_reset(reset, now, task.get('resetDays'))
    task['resetSchedule'] = '11amEST'


def apply_resets(state, records, now=None):
    now = time.time() if now is None else now
    changed = False
    for tasks in state.values():
        for task in tasks:
            if is_automatic(task) or task.get('reset') not in ('Daily', 'Weekly', 'Custom'):
                continue
            due = next_reset(task['reset'], task.get('changedAt', now), task.get('resetDays'))
            if task.get('resetSchedule') != '11amEST' or task.get('resetAt') != due:
                task.update(resetAt=due, resetSchedule='11amEST')
                changed = True
            if due and now >= due:
                task.update(status='Pending', resetAt=next_reset(task['reset'], now, task.get('resetDays')), changedAt=now)
                changed = True
    return changed


def merge_addon(conn, records):
    """Merge saved addon edits by timestamp, including deletions from either side."""
    state = load(conn)
    removed = db.get_json(conn, 'quest_log_deleted') or {}
    changed = False
    for record in records:
        guid = record.get('guid')
        if not guid or not record.get('todos') and not record.get('todoDeleted'):
            continue
        tasks = state.setdefault(guid, [])
        for ident, stamp in (record.get('todoDeleted') or {}).items():
            old = next((t for t in tasks if t['id'] == ident), None)
            if old and stamp >= old.get('changedAt', 0):
                tasks.remove(old)
                changed = True
        incoming_tasks = record.get('todos') or []
        if isinstance(incoming_tasks, dict):
            incoming_tasks = list(incoming_tasks.values())
        for incoming in incoming_tasks:
            task = copy.deepcopy(incoming)
            if isinstance(task.get('resetDays'), dict):
                task['resetDays'] = list(task['resetDays'].values())
            ident = task.get('id')
            if not ident or (removed.get(guid) or {}).get(ident, 0) >= task.get('changedAt', task.get('created', 0)):
                continue
            task.setdefault('title', task.get('text', ''))
            task.setdefault('status', 'Completed' if task.get('done') else 'Pending')
            task.setdefault('changedAt', task.get('created', 0))
            old = next((t for t in tasks if t['id'] == ident), None)
            if old is None:
                tasks.append(task)
                changed = True
            elif task['changedAt'] > old.get('changedAt', 0):
                old.update(task)
                changed = True
    if changed:
        db.set_json(conn, STATE_KEY, state)
    return state, removed


def is_automatic(task):
    return any(task.get(key) for key in ('questID', 'achievementID', 'itemID'))


def task_caption(task, record):
    """Compact reset and priority markers shared with the addon task headings."""
    reset = task_reset(task, record)
    marker = ' [D]' if reset == 'Daily' else ' [W]' if reset == 'Weekly' else (
        ' [' + ','.join(str(day) for day in task.get('resetDays', [])) + ']'
        if reset == 'Custom' and task.get('resetDays') else '')
    priority = '1' if task.get('priority') == 'High' else '3' if task.get('priority') == 'Low' else '2'
    return task_name(task, record) + marker + ' [' + priority + ']'
