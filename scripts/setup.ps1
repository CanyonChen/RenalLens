# Set up RenalLens on Windows, including machines without Python or uv.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectConfig = Get-Content -LiteralPath (Join-Path $projectRoot 'pyproject.toml') -Raw
$uvVersion = [regex]::Match($projectConfig, '(?m)^required-version\s*=\s*"==([^"]+)"').Groups[1].Value
if (-not $uvVersion) {
    throw 'Expected an exact tool.uv.required-version in pyproject.toml.'
}

$userBin = Join-Path $env:USERPROFILE '.local\bin'
$uv = Join-Path $userBin 'uv.exe'
$existingUv = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue
if ($existingUv) {
    $uv = $existingUv.Source
}

$installedVersion = ''
if (Test-Path -LiteralPath $uv) {
    $installedVersion = (& $uv --version)
}

Push-Location -LiteralPath $projectRoot
$previousProjectEnvironment = $env:UV_PROJECT_ENVIRONMENT
try {
    if ($installedVersion -notmatch ('^uv ' + [regex]::Escape($uvVersion) + '(\s|$)')) {
        Write-Host "Installing uv $uvVersion for the current user..."
        New-Item -ItemType Directory -Force -Path '.cache' | Out-Null
        $installer = Join-Path $projectRoot '.cache\uv-installer.ps1'
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri "https://astral.sh/uv/$uvVersion/install.ps1" -OutFile $installer
        $previousInstallDir = $env:UV_INSTALL_DIR
        try {
            $env:UV_INSTALL_DIR = $userBin
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
            if ($LASTEXITCODE -ne 0) { throw 'The uv installer failed.' }
        } finally {
            $env:UV_INSTALL_DIR = $previousInstallDir
        }
        $uv = Join-Path $userBin 'uv.exe'
    }

    $env:Path = (Split-Path -Parent $uv) + ';' + $env:Path
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $projectRoot '.venv'
    & $uv --version
    if ($LASTEXITCODE -ne 0) { throw 'Could not run uv.' }

    Write-Host 'Synchronizing the locked Python environment (including Jupyter)...'
    & $uv sync --locked
    if ($LASTEXITCODE -ne 0) { throw 'Environment synchronization failed.' }

    & $uv pip check --python (Join-Path $projectRoot '.venv\Scripts\python.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency compatibility check failed.' }

    Write-Host 'Checking Python and importing the project libraries...'
    @'
from pathlib import Path
import platform
import numpy, pandas, scipy, matplotlib, seaborn, sklearn, ipykernel, jupyterlab

expected = Path('.python-version').read_text().strip()
actual = platform.python_version()
if actual != expected:
    raise SystemExit(f'Python mismatch: expected {expected}, got {actual}')
print(f'Environment OK: Python {actual}; all 8 project libraries imported.')
'@ | & $uv run --locked python -
    if ($LASTEXITCODE -ne 0) { throw 'Environment import check failed.' }

    Write-Host ''
    Write-Host 'Setup complete. In VS Code, select .venv\Scripts\python.exe.'
    Write-Host 'Restart VS Code or open a new standalone terminal, then use: uv run --locked jupyter lab'
} finally {
    $env:UV_PROJECT_ENVIRONMENT = $previousProjectEnvironment
    Pop-Location
}
