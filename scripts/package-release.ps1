# Package the addon and built Companion with neutral sync files.
param([string]$ReleaseTag = 'v2.2.1')
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$tocPath = Join-Path $repositoryRoot 'AltTrackingAssistant.toc'
$versionLine = Get-Content -LiteralPath $tocPath | Where-Object { $_ -match '^## Version:' } | Select-Object -First 1
$version = ($versionLine -replace '^## Version:\s*', '').Trim()
if ($ReleaseTag -cne "v$version") { throw "Release tag $ReleaseTag does not match TOC version $version." }
$stagingRoot = Join-Path $repositoryRoot ("build/release-$ReleaseTag-" + [guid]::NewGuid().ToString('N'))
$packageDir = Join-Path $stagingRoot 'AltTrackingAssistant'
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
foreach ($folder in @('Core', 'Features', 'Media', 'UI')) {
    Copy-Item -LiteralPath (Join-Path $repositoryRoot $folder) -Destination $packageDir -Recurse
}
foreach ($file in @('AltTrackingAssistant.toc', 'AltTrackingAssistantCompanion.exe', 'README.md', 'CHANGELOG.md', 'RELEASE_NOTES.md', 'LICENSE')) {
    Copy-Item -LiteralPath (Join-Path $repositoryRoot $file) -Destination $packageDir
}
foreach ($name in @('AppSync', 'QuestSync', 'NotesSync')) {
    Copy-Item -LiteralPath (Join-Path $repositoryRoot "scripts/$name.default.lua") -Destination (Join-Path $packageDir "$name.lua")
}
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'Companion/README.md') -Destination (Join-Path $packageDir 'Companion-README.md')
$companionDocs = Join-Path $packageDir 'Companion'
New-Item -ItemType Directory -Path $companionDocs -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'Companion/README.md') -Destination (Join-Path $companionDocs 'README.md')
$zipPath = Join-Path $repositoryRoot "AltTrackingAssistant-$ReleaseTag.zip"
Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -Force
Write-Host "Release package: $zipPath"
Write-Host "Staged folder: $packageDir"
