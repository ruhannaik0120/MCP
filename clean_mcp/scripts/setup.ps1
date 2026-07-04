$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $ProjectRoot
$Venv = Join-Path $WorkspaceRoot ".venv"

if (Test-Path $Venv) {
    $Python = Join-Path $Venv "Scripts\python.exe"
    & $Python --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Recurse -Force $Venv
    }
}

if (-not (Test-Path $Venv)) {
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        & py -3 -m venv $Venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment with py." }
    } else {
        $PythonCommand = Get-Command python -ErrorAction Stop
        & $PythonCommand.Source -m venv $Venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment with python." }
    }
}

$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install project dependencies." }
Write-Host "Environment ready: $Python"
