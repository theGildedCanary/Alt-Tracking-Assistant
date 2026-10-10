"""Verify the packaged GUI and exports on a hosted Mac, without a WoW install."""

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook


def verify(bundle):
    executable = Path(bundle).resolve() / "Contents" / "MacOS" / "AltTrackingAssistantCompanion"
    subprocess.run([str(executable), "--smoke-test"], check=True, timeout=60)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        saved = root / "World of Warcraft" / "_retail_" / "WTF" / "Account" / "TEST#1" / "SavedVariables"
        saved.mkdir(parents=True)
        (saved / "AltTrackingAssistant.lua").write_text(
            'AltTrackingAssistantDB = { ["characters"] = { ["Player-1-Test"] = { '
            '["name"] = "MacTest", ["realm"] = "Test Realm", ["classFile"] = "MAGE", '
            '["class"] = "Mage", ["level"] = 80, ["lastScanned"] = 1, '
            '["progress"] = {} } } }', encoding="utf-8",
        )
        for suffix in ("csv", "xlsx"):
            output = root / f"export.{suffix}"
            subprocess.run([str(executable), "--export", str(root / "World of Warcraft"), str(output)],
                           check=True, timeout=60)
            if suffix == "csv":
                with output.open(encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.reader(stream))
            else:
                workbook = load_workbook(output, read_only=True)
                try:
                    rows = list(workbook["Alt Tracking Assistant"].values)
                finally:
                    workbook.close()
            if len(rows) != 2 or rows[1][0] != "MacTest":
                raise RuntimeError(f"Packaged {suffix} export failed validation: {rows!r}")
    print("Packaged Mac GUI and CSV/XLSX exports passed.")


if __name__ == "__main__":
    verify(sys.argv[1])
