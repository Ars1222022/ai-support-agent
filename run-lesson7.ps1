$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Phoenix = Join-Path $Root ".venv\Scripts\phoenix.exe"
if (-not (Test-Path $Python) -or -not (Test-Path $Phoenix)) { throw "Lokal miljö saknas. Kör först ./setup-lesson7.ps1" }
New-Item -ItemType Directory -Force (Join-Path $Root ".runtime\huggingface"), (Join-Path $Root ".runtime\phoenix") | Out-Null
$env:HF_HOME = Join-Path $Root ".runtime\huggingface"
$env:PHOENIX_WORKING_DIR = Join-Path $Root ".runtime\phoenix"
$env:PHOENIX_COLLECTOR_ENDPOINT = "http://localhost:6006"
$outLog = Join-Path $Root ".runtime\phoenix-out.log"
$errLog = Join-Path $Root ".runtime\phoenix-error.log"
$PhoenixProcess = Start-Process -FilePath $Phoenix -ArgumentList @("serve", "--host", "127.0.0.1", "--port", "6006") -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
try {
    $Ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        if ($PhoenixProcess.HasExited) { throw "Phoenix stannade. Läs .runtime/phoenix-error.log" }
        try { Invoke-WebRequest -Uri "http://localhost:6006" -TimeoutSec 2 | Out-Null; $Ready = $true; break } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $Ready) { throw "Phoenix startade inte på port 6006. Läs .runtime/phoenix-error.log" }
    Write-Host "Phoenix körs på http://localhost:6006. Appen: http://localhost:8501" -ForegroundColor Green
    & $Python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
    if ($LASTEXITCODE -ne 0) { throw "Streamlit avslutades med fel." }
} finally {
    if (-not $PhoenixProcess.HasExited) { Stop-Process -Id $PhoenixProcess.Id -Force }
}
