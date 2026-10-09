# Builds dist\AltTrackingAssistantCompanion.exe (requires: python -m pip install pyinstaller -r requirements.txt)
# Place client_secret.json (Google OAuth Desktop client) in this folder first so Google sign-in works for end users.
if (-not (Test-Path client_secret.json)) { Write-Warning 'client_secret.json not found: Google sign-in will not work in this build.' }
$bundle = if (Test-Path client_secret.json) { @('--add-data', 'client_secret.json;.') } else { @() }
python -m PyInstaller --noconfirm --onefile --windowed --name AltTrackingAssistantCompanion --collect-data googleapiclient --icon ATAIcon.ico --add-data 'fonts;fonts' --add-data 'ATAIcon.ico;.' @bundle app.py
