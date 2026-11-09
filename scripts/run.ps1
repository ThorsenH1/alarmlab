param(
    [ValidateSet('Demo', 'Test', 'Run', 'Setup')]
    [string]$Action = 'Demo',
    [string]$PythonPath = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $projectRoot
if ($Action -eq 'Demo') {
    Invoke-Item -LiteralPath (Join-Path $projectRoot 'demo\index.html')
    return
}
$candidates = @()
if ($PythonPath) { $candidates += $PythonPath }
$candidates += (Join-Path $projectRoot '.venv\Scripts\python.exe')
$localPythonRoots = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python')
)
foreach ($localPythonRoot in ($localPythonRoots | Select-Object -Unique)) {
    if (Test-Path -LiteralPath $localPythonRoot) {
        $candidates += @(Get-ChildItem -LiteralPath $localPythonRoot -Filter python.exe -File -Recurse | Select-Object -ExpandProperty FullName)
    }
}
$candidates += @('python', 'py')
$selectedPython = $null
foreach ($candidate in $candidates) {
    try {
        & $candidate -c 'import sys; assert sys.version_info >= (3,11)' 2>$null
        if ($LASTEXITCODE -eq 0) { $selectedPython = $candidate; break }
    } catch { }
}
if (-not $selectedPython) { throw 'Python 3.11+ was not found. Supply -PythonPath with the interpreter path.' }
if ($Action -eq 'Setup') {
    & $selectedPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }
    $selectedPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $selectedPython -m pip install -r requirements-tested.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $selectedPython -m pip install --no-deps -e .
    if ($LASTEXITCODE -ne 0) { throw 'Package installation failed.' }
    return
}
$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $projectRoot 'src'
    if ($Action -eq 'Test') {
        & $selectedPython -m unittest discover -s tests -v
    } else {
        & $selectedPython run.py all --output artifacts/rerun --demo artifacts/rerun/demo
    }
    if ($LASTEXITCODE -ne 0) { throw 'The requested command failed; see the output above.' }
} finally {
    $env:PYTHONPATH = $previousPythonPath
}
