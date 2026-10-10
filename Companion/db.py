"""Local SQLite database holding every character the companion has seen."""

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("APPDATA", Path.home())) / "AltTrackingAssistantCompanion" / "companion.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    guid TEXT PRIMARY KEY,
    name TEXT,
    realm TEXT,
    class_name TEXT,
    class_file TEXT,
    race TEXT,
    body_type INTEGER,
    account TEXT,
    faction TEXT,
    level INTEGER,
    level10_date INTEGER,
    last_scanned INTEGER NOT NULL DEFAULT 0,
    is_main INTEGER NOT NULL DEFAULT 0,
    progress_json TEXT NOT NULL DEFAULT '{}',
    professions_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    if "body_type" not in {row[1] for row in conn.execute("PRAGMA table_info(characters)")}:
        conn.execute("ALTER TABLE characters ADD COLUMN body_type INTEGER")
    if "account" not in {row[1] for row in conn.execute("PRAGMA table_info(characters)")}:
        conn.execute("ALTER TABLE characters ADD COLUMN account TEXT")
    if "professions_json" not in {row[1] for row in conn.execute("PRAGMA table_info(characters)")}:
        conn.execute("ALTER TABLE characters ADD COLUMN professions_json TEXT DEFAULT '{}'")
    return conn


def get_json(conn, key):
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else None


def set_json(conn, key, value):
    with conn:
        if value is None:
            conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))
        else:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(value)),
            )


def main_guids(settings):
    """Characters picked as a main in the addon's character-main slots (armor mains are excluded)."""
    mains = (settings or {}).get("characterMains") or {}
    mode = mains.get("characterMode") or "single"
    prefix = "single" if mode == "single" else mode + ":"
    selections = mains.get("selections") or {}
    return {
        guid
        for slot, guid in selections.items()
        if isinstance(guid, str) and (slot == prefix or str(slot).startswith(prefix))
    }


def _int_or_none(value):
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def sync_characters(conn, characters, mains):
    """Insert or refresh characters from the addon data. Characters missing from the addon stay in the database."""
    with conn:
        for guid, record in characters.items():
            conn.execute(
                """
                INSERT INTO characters (guid, name, realm, class_name, class_file, race, body_type, account, faction, level,
                                        level10_date, last_scanned, progress_json, professions_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guid) DO UPDATE SET
                    name = excluded.name, realm = excluded.realm, class_name = excluded.class_name,
                    class_file = excluded.class_file, race = excluded.race,
                    body_type = COALESCE(excluded.body_type, characters.body_type),
                    account = excluded.account, faction = excluded.faction,
                    level = excluded.level, level10_date = excluded.level10_date,
                    last_scanned = excluded.last_scanned, progress_json = excluded.progress_json,
                    professions_json = COALESCE(excluded.professions_json, characters.professions_json)
                WHERE excluded.last_scanned >= characters.last_scanned
                """,
                (
                    str(guid),
                    record.get("name"),
                    record.get("realm"),
                    record.get("class"),
                    record.get("classFile"),
                    record.get("race"),
                    _int_or_none(record.get("bodyType")),
                    record.get("account"),
                    record.get("faction"),
                    _int_or_none(record.get("level")),
                    _int_or_none(record.get("level10Date")),
                    _int_or_none(record.get("lastScanned")) or 0,
                    json.dumps(record.get("progress") or {}),
                    json.dumps(record["professions"]) if isinstance(record.get("professions"), dict) else None,
                ),
            )
        conn.execute("UPDATE characters SET is_main = 0")
        conn.executemany("UPDATE characters SET is_main = 1 WHERE guid = ?", [(str(g),) for g in mains])


def load_characters(conn):
    """Characters as dicts using the same field names as the addon's saved records."""
    result = []
    for row in conn.execute("SELECT * FROM characters"):
        result.append(
            {
                "guid": row["guid"],
                "name": row["name"],
                "realm": row["realm"],
                "class": row["class_name"],
                "classFile": row["class_file"],
                "race": row["race"],
                "bodyType": row["body_type"],
                "account": row["account"],
                "faction": row["faction"],
                "level": row["level"],
                "level10Date": row["level10_date"],
                "lastScanned": row["last_scanned"],
                "isMain": bool(row["is_main"]),
                "progress": json.loads(row["progress_json"] or "{}"),
                "professions": json.loads(row["professions_json"] or "{}"),
            }
        )
    return result
