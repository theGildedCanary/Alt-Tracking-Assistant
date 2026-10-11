"""Roster-style quest columns and four-state indicators."""
import theme
import quest_log as model
from grid import Cell, Column

INDICATORS = {
    'Pending': ('☐', theme.GOLD),
    'Not picked up': ('○', theme.MUTED_TEXT),
    'Picked up': ('☐', theme.GOLD),
    'In progress': ('☐', theme.GOLD),
    'Completed': ('☑', theme.GOLD),
}
GROUP_COLORS = {
    'Weeklies': '#331e53',
    'Dailies': '#18365b',
    'Other quests': theme.PANEL_ALT,
    'To dos': '#1e462c',
}
GROUP_ACCENTS = {group: '#ffffff' for group in GROUP_COLORS}


def build_grid(state, records, selected=None, now=None):
    catalog = {}
    for guid, tasks in state.items():
        for task in tasks:
            if not task.get('questID'):
                continue
            data = model.snapshot(task, records.get(guid, {}))
            entry = dict(id=task['questID'], name=model.task_name(task, records.get(guid, {})), nickname=task.get('title'),
                         reset=model.task_reset(task, records.get(guid, {})), stamp=data.get('scannedAt', 0))
            old = catalog.get(task['questID'])
            if not old or (entry['reset'] != 'Unknown' and (old['reset'] == 'Unknown' or entry['stamp'] >= old['stamp'])):
                catalog[task['questID']] = entry
            if task.get('title'):
                catalog[task['questID']]['name'] = task['title']
                catalog[task['questID']]['nickname'] = task['title']
            elif old and old.get('nickname'):
                catalog[task['questID']]['name'] = old['nickname']
                catalog[task['questID']]['nickname'] = old['nickname']
    quests = sorted(catalog.values(), key=lambda q: (('Weekly', 'Daily', 'None', 'Unknown').index(q['reset'])
                    if q['reset'] in ('Weekly', 'Daily', 'None', 'Unknown') else 4, q['name'].casefold(), q['id']))
    for reset in ('Weekly', 'Daily'):
        if not any(q['reset'] == reset for q in quests):
            quests.append(dict(id=None, name='No quests', reset=reset, stamp=0))
    quests.sort(key=lambda q: (0 if q['reset'] == 'Weekly' else 1 if q['reset'] == 'Daily' else 2,
                              q['name'].casefold(), q['id'] or 0))
    columns = [Column('', 24, frozen=True, bg=theme.PANEL, fixed_width=24),
               Column('Character', 200, frozen=True, fg=theme.GOLD),
               Column('To do', 80, frozen=True, align='center', fg=theme.GOLD)]
    manuals = {}
    for tasks in state.values():
        for task in tasks:
            if not task.get('questID'):
                manuals.setdefault(model.assignment_key(task), task)
    manual_columns = sorted(manuals, key=lambda key: (manuals[key]['title'].casefold(), key[1]))
    for quest in quests:
        group = {'Weekly': 'Weeklies', 'Daily': 'Dailies'}.get(quest['reset'], 'Other quests')
        column = Column(quest['name'], 44, group=group, group_key=group, vertical=True,
                        align='center', title_fg=GROUP_ACCENTS[group], fg=GROUP_ACCENTS[group], bg=GROUP_COLORS[group])
        column.quest_id = quest['id']
        columns.append(column)
    for key in manual_columns:
        column = Column(manuals[key]['title'], 44, group='To dos', group_key='To dos', vertical=True,
                        align='center', title_fg=GROUP_ACCENTS['To dos'], fg=GROUP_ACCENTS['To dos'], bg=GROUP_COLORS['To dos'])
        column.task_key = key
        columns.append(column)
    rows, guids = [], list(state)
    for guid in guids:
        record = records.get(guid, {})
        tasks = state[guid]
        bg = theme.UI_THEMES['WoW Mode']['selected'] if guid == selected else ''
        manual = [t for t in tasks if not t.get('questID')]
        class_bg = theme.CLASS_COLORS.get(record.get('classFile'), bg)
        if class_bg.upper() == '#FFFFFF':
            class_bg = theme.MUTED_TEXT
        row = [Cell(bg=theme.PANEL, removable=True),
               Cell(f"{record.get('level') or '?'} - {record.get('name', 'Unavailable character')}", bg=class_bg, fg='#000000'),
               Cell(f"{sum(model.task_status(t, record, now) == 'Completed' for t in manual)}/{len(manual)}", fg=theme.GOLD, bg=bg)]
        assigned = {t['questID']: t for t in tasks if t.get('questID')}
        for quest in quests:
            task = assigned.get(quest['id'])
            checked = None
            if task:
                status = model.task_status(task, record, now)
                symbol, color = INDICATORS.get(status, ('?', theme.MUTED_TEXT))
                if status in ('Picked up', 'In progress', 'Completed'):
                    checked = status == 'Completed'
            else:
                symbol, color = '—', theme.DIVIDER
            row.append(Cell(symbol, fg=color, bg=bg, checked=checked))
        assigned_manual = {model.assignment_key(t): t for t in manual}
        for key in manual_columns:
            task = assigned_manual.get(key)
            symbol, color = INDICATORS.get(model.task_status(task, record, now), ('?', theme.MUTED_TEXT)) if task else ('—', theme.DIVIDER)
            row.append(Cell(symbol if not task else '', fg=color, bg=bg,
                            checked=model.task_status(task, record, now) == 'Completed' if task else None))
        row.extend(Cell('—', fg=theme.DIVIDER, bg=bg) for _ in range(len(columns) - len(row)))
        rows.append(row)
    return columns, rows, guids
