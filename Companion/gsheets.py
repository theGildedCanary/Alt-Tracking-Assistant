"""Google Sheets export using the OAuth installed-app flow."""

import json
import os
import re
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CLIENT_FILE = "client_secret.json"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "AltTrackingAssistantCompanion"
TOKEN_PATH = CONFIG_DIR / "google_token.json"
TAB_NAME = "Alt Tracking Assistant"

_ID_PATTERN = re.compile(r"/spreadsheets/d/([A-Za-z0-9_-]+)")


class GoogleSheetsError(Exception):
    pass


def parse_spreadsheet_id(value):
    value = (value or "").strip()
    match = _ID_PATTERN.search(value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
        return value
    raise GoogleSheetsError("Enter a valid Google Sheets URL.")


def find_client_file():
    """Look in the bundled resources, next to the executable/script, then the config folder."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / CLIENT_FILE)
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / CLIENT_FILE)
    candidates.append(Path(__file__).resolve().parent / CLIENT_FILE)
    candidates.append(CONFIG_DIR / CLIENT_FILE)
    return next((p for p in candidates if p.is_file()), None)


def is_signed_in():
    return TOKEN_PATH.is_file()


def sign_out():
    try:
        TOKEN_PATH.unlink()
    except FileNotFoundError:
        pass


def get_credentials(interactive=True):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except ValueError:
            creds = None
    if creds and creds.valid:
        return creds
    if creds and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except RefreshError:
            sign_out()
    if not interactive:
        raise GoogleSheetsError("Google sign-in expired. Click 'Sign in with Google' again.")

    client_file = find_client_file()
    if not client_file:
        raise GoogleSheetsError(
            "Google sign-in is not set up in this build of the app (client_secret.json is missing)."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", timeout_seconds=180)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def write_to_sheet(spreadsheet_url, header, rows, interactive=True):
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    spreadsheet_id = parse_spreadsheet_id(spreadsheet_url)
    service = build("sheets", "v4", credentials=get_credentials(interactive), cache_discovery=False)
    sheets = service.spreadsheets()
    try:
        meta = sheets.get(spreadsheetId=spreadsheet_id, fields="sheets.properties").execute()
        existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
        if TAB_NAME in existing:
            tab_id = existing[TAB_NAME]
        else:
            reply = sheets.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": TAB_NAME}}}]},
            ).execute()
            tab_id = reply["replies"][0]["addSheet"]["properties"]["sheetId"]

        quoted = f"'{TAB_NAME}'"
        sheets.values().clear(spreadsheetId=spreadsheet_id, range=quoted, body={}).execute()
        sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{quoted}!A1",
            valueInputOption="RAW",
            body={"values": [header] + [list(r) for r in rows]},
        ).execute()
        sheets.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": tab_id,
                                "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 2},
                            },
                            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                            "fields": "userEnteredFormat.textFormat.bold",
                        }
                    },
                    {"autoResizeDimensions": {"dimensions": {"sheetId": tab_id, "dimension": "COLUMNS"}}},
                ]
            },
        ).execute()
    except HttpError as error:
        raise GoogleSheetsError(_explain(error)) from error


def _explain(error):
    status = getattr(error.resp, "status", None)
    try:
        detail = json.loads(error.content.decode("utf-8"))["error"].get("message", "")
    except (ValueError, KeyError, AttributeError):
        detail = str(error)
    lowered = detail.lower()
    if "has not been used" in lowered or "is disabled" in lowered:
        return "The Google Sheets API is not enabled for this app's Google Cloud project. " + detail
    if "not supported for this document" in lowered:
        return (
            "This file is an uploaded Excel file, not a native Google Sheet. "
            "In Google Sheets choose File > Save as Google Sheets, then use the new file's link. " + detail
        )
    if status == 404:
        return "Sheet not found. Check the link. " + detail
    if status == 403:
        return "Google denied access (the signed-in account may not match the sheet's owner). " + detail
    return f"Google Sheets error ({status}): {detail}"
