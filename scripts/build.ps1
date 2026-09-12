$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Copy-ModelDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing bundled model assets: $Source"
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Copy-Item -Path (Join-Path $Source "*") -Destination $Destination -Recurse -Force
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Create it with: py -3.12 -m venv .venv"
}

Push-Location $projectRoot
try {
    & $python -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m PyInstaller --noconfirm --clean onflytranslator.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Copy-Item -LiteralPath "config.json" -Destination "dist\BellenneRelay\config.json" -Force
    Copy-ModelDirectory `
        -Source "model_assets\whisper\turbo" `
        -Destination "dist\BellenneRelay\models\whisper\turbo"
    Copy-ModelDirectory `
        -Source "model_assets\translation\en-ru" `
        -Destination "dist\BellenneRelay\models\translation\en-ru"
    Copy-ModelDirectory `
        -Source "model_assets\translation\ru-en" `
        -Destination "dist\BellenneRelay\models\translation\ru-en"
    Write-Host "Build ready: dist\BellenneRelay\BellenneRelay.exe"
}
finally {
    Pop-Location
}
