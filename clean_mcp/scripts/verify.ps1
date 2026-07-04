$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $ProjectRoot
$Python = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment missing. Run clean_mcp\scripts\setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $Python -m compileall -q .
    if ($LASTEXITCODE -ne 0) { throw "Compilation failed." }
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Test suite failed." }
    $env:DB_TYPE = "demo"
    $env:DB_DATABASE = "qa_demo"
    $env:DB_EXECUTION_MODE = "read_only"
    & $Python tests\smoke_test.py
    if ($LASTEXITCODE -ne 0) { throw "Smoke test failed." }
    Write-Host "All verification gates passed."
} finally {
    Pop-Location
}
