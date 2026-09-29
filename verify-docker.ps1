$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root
$Failed = $false
Write-Host "=== Compose configuration ===" -ForegroundColor Cyan
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: Compose config" -ForegroundColor Red; $Failed = $true } else { Write-Host "PASS: Compose config" -ForegroundColor Green }

Write-Host "=== Service status ===" -ForegroundColor Cyan
docker compose ps
if ($LASTEXITCODE -ne 0) { $Failed = $true }
$Running = docker compose ps --status running --services
if ($LASTEXITCODE -ne 0 -or -not ($Running -contains "lesson7")) {
    Write-Host "FAIL: lesson7 kör inte. Starta först med: docker compose up --build -d" -ForegroundColor Red
    $Failed = $true
}

if (-not $Failed) {
    Write-Host "=== Imports inside app container ===" -ForegroundColor Cyan
    docker compose exec -T lesson7 python -c "import streamlit, openai, langgraph, chromadb, sentence_transformers, phoenix.otel; import openinference.instrumentation.openai; print('PASS: Python dependencies')"
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: app imports" -ForegroundColor Red; $Failed = $true }
    if (-not $Failed) {
        Write-Host "=== RAG, Chroma, LangGraph and offline eval ===" -ForegroundColor Cyan
        docker compose exec -T lesson7 python smoke_test.py
        if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: offline smoke test" -ForegroundColor Red; $Failed = $true }
    }
}

Write-Host "=== Service HTTP checks ===" -ForegroundColor Cyan
foreach ($Check in @(@{Name="app"; Url="http://localhost:8501/_stcore/health"}, @{Name="Chroma"; Url="http://localhost:8000/api/v2/heartbeat"}, @{Name="Phoenix"; Url="http://localhost:6006"})) {
    try { $null = Invoke-WebRequest -Uri $Check.Url -TimeoutSec 5; Write-Host "PASS: $($Check.Name) $($Check.Url)" -ForegroundColor Green }
    catch { Write-Host "FAIL: $($Check.Name) — $($_.Exception.Message)" -ForegroundColor Red; $Failed = $true }
}

if ($Failed) {
    Write-Host "=== Recent logs ===" -ForegroundColor Yellow
    docker compose logs --tail 80 lesson7 chroma phoenix
    Write-Host "Tips: kontrollera tjänster med 'docker compose ps -a' och åtgärda första ERROR-raden i loggen." -ForegroundColor Yellow
    exit 1
}
Write-Host "Alla lokala containerkontroller godkända. LLM kräver giltig API-nyckel." -ForegroundColor Green
