param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Push-Location -LiteralPath $projectDir
try {
    & $Python -m PyInstaller --noconfirm --clean transcriber.spec
    if ($LASTEXITCODE -ne 0) { throw 'Transcription worker build failed.' }
    & $Python -m PyInstaller --noconfirm --clean ReelsMakerPro.spec
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
    $workerSource = Join-Path $projectDir 'dist\transcriber'
    $workerTarget = Join-Path $projectDir 'dist\ReelsMakerPro\transcriber'
    Copy-Item -LiteralPath $workerSource -Destination $workerTarget -Recurse -Force
    if (-not (Test-Path -LiteralPath (Join-Path $workerTarget 'rm-transcribe.exe'))) {
        throw 'The application bundle is missing its transcription worker.'
    }
    Write-Output 'Complete application bundle: dist\ReelsMakerPro'
} finally {
    Pop-Location
}
