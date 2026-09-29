$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Lokal miljö saknas. Kör ./setup-lesson7.ps1 först." }
$Failed = $false
Write-Host "=== Offline RAG/Chroma/LangGraph/eval check ===" -ForegroundColor Cyan
& $Python smoke_test.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: smoke test" -ForegroundColor Red; $Failed = $true }
foreach ($Check in @(@{Name="app"; Url="http://localhost:8501/_stcore/health"}, @{Name="Phoenix"; Url="http://localhost:6006"})) {
    try { $null = Invoke-WebRequest -Uri $Check.Url -TimeoutSec 5; Write-Host "PASS: $($Check.Name) HTTP" -ForegroundColor Green }
    catch { Write-Host "FAIL: $($Check.Name) svarar inte — $($_.Exception.Message)" -ForegroundColor Red; $Failed = $true }
}
if ($Failed) {
    Write-Host "Kontrollera terminalen där run-lesson7.ps1 körs. Phoenix-loggar finns i .runtime/phoenix-error.log och .runtime/phoenix-out.log." -ForegroundColor Yellow
    exit 1
}
Write-Host "Lokala beroenden, RAG, Chroma, LangGraph, evals, app och Phoenix verifierades." -ForegroundColor Green
