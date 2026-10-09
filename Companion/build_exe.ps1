# Builds AltTrackingAssistantCompanion.exe in the main addon folder.
# Requires: python -m pip install pyinstaller -r requirements.txt
param([string]$PythonExecutable = 'python')

$ErrorActionPreference = 'Stop'
$outputDir = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $PSScriptRoot
try {
    & $PythonExecutable -m PyInstaller --noconfirm --clean --onefile --windowed --name AltTrackingAssistantCompanion --distpath $outputDir --icon ATAIcon.ico --add-data 'fonts;fonts' --add-data 'ATAIcon.ico;.' app.py
    if ($LASTEXITCODE -ne 0) { throw "Companion build failed with exit code $LASTEXITCODE." }
    Write-Host "Built $(Join-Path $outputDir 'AltTrackingAssistantCompanion.exe')"
}
finally {
    Pop-Location
}
