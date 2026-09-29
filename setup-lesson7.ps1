$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root
$env:PIP_NO_CACHE_DIR = "1"

function Invoke-Checked { param([string]$Exe, [string[]]$Parameters)
    & $Exe @Parameters
    if ($LASTEXITCODE -ne 0) { throw "Kommandot misslyckades: $Exe $($Parameters -join ' ')" }
}

$Launcher = Get-Command py -ErrorAction SilentlyContinue
if ($Launcher) {
    $Python = $Launcher.Source
    Invoke-Checked $Python @("-3.12", "--version")
    $VenvArgs = @("-3.12", "-m", "venv", ".venv")
    $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
} else {
    $Launcher = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Launcher) { throw "Python 3.12 saknas. Installera Python 3.12 och markera 'Add Python to PATH', öppna sedan en ny terminal." }
    $Python = $Launcher.Source
    $Version = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($Version -ne "3.12") { throw "Python 3.12 krävs. Hittade $Version. Installera Python 3.12 eller använd Python Launcher: py -3.12." }
    $VenvArgs = @("-m", "venv", ".venv")
    $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
}

if (-not (Test-Path $VenvPython)) { Invoke-Checked $Python $VenvArgs }
$VenvVersion = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($VenvVersion -ne "3.12") { throw ".venv innehåller Python $VenvVersion. Flytta eller ta bort endast projektets .venv-mapp och kör skriptet igen." }
New-Item -ItemType Directory -Force (Join-Path $Root ".runtime\huggingface"), (Join-Path $Root ".runtime\chroma"), (Join-Path $Root ".runtime\phoenix") | Out-Null
Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $VenvPython @("-m", "pip", "install", "--no-cache-dir", "--index-url", "https://download.pytorch.org/whl/cpu", "torch==2.10.0+cpu")
Invoke-Checked $VenvPython @("-m", "pip", "install", "--no-cache-dir", "-r", "requirements-local.txt")
Invoke-Checked $VenvPython @("-c", "import streamlit, openai, langgraph, chromadb, sentence_transformers, phoenix.otel; import openinference.instrumentation.openai; print('Alla kursberoenden importerades OK')")

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
Write-Host "Klar. Projektmiljön finns i .venv och modeller/data sparas under .runtime." -ForegroundColor Green
Write-Host "Lägg till en API-nyckel i .env om du vill testa LLM-svar. Starta med: ./run-lesson7.ps1"
