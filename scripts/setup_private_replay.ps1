# One-time isolated Windows parity runner. Does not change the B-BOT venv or R4 host.
param(
  [Parameter(Mandatory=$true)][string]$ResearchZip,
  [Parameter(Mandatory=$true)][string]$EngineCacheZip,
  [Parameter(Mandatory=$true)][string]$ModulesZip,
  [switch]$Execute,
  [string]$OutputDir = ""
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$archives = @($ResearchZip, $EngineCacheZip, $ModulesZip) | ForEach-Object {
    (Resolve-Path $_).Path
}
$venv = Join-Path $root ".private-replay-venv"
if (-not (Test-Path (Join-Path $venv "Scripts/python.exe"))) {
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create isolated venv" }
}
$python = Join-Path $venv "Scripts/python.exe"
& $python -m pip install --disable-pip-version-check -r (Join-Path $root "requirements-research-ci.txt")
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed; formal runner not started" }
& $python -c "import pyarrow,pandas,numpy,optuna; print('PYARROW_VERSION',pyarrow.__version__)"
if ($LASTEXITCODE -ne 0) { throw "PyArrow import failed" }
$argsList = @((Join-Path $root "scripts/staged_official_replay.py")) + $archives
if ($Execute) {
    if (-not $OutputDir) { throw "Specify -OutputDir for retained official backtest reports" }
    $argsList += @("--execute", "--output-dir", $OutputDir)
}
& $python @argsList
if ($LASTEXITCODE -ne 0) { throw "Official replay/staging failed (exit code $LASTEXITCODE)" }
Write-Host "PASS: isolated runner finished. Execute flag was: $Execute"
