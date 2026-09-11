# ARIA - Start-Workflow

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot

function Wait-ForHealth {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSeconds = 180
    )
    Write-Host "Warte auf $Name ($Url)..." -ForegroundColor DarkGray
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        try {
            Invoke-RestMethod -Uri $Url -TimeoutSec 3 | Out-Null
            Write-Host "$Name ist bereit." -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Seconds 2
            $elapsed += 5
        }
    }
    Write-Host "$Name antwortet nach $TimeoutSeconds Sekunden nicht - bitte manuell pruefen." -ForegroundColor Yellow
    return $false
}

function Wait-ForDockerDesktop {
    param([int]$TimeoutSeconds = 90)
    try { docker info *> $null } catch {}
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker-Desktop laeuft bereits." -ForegroundColor Green
        return $true
    }
    Write-Host "Docker Desktop laeuft nicht - starte es..." -ForegroundColor Yellow
    $dockerDesktopExe = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"
    Start-Process $dockerDesktopExe

    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        try { docker info *> $null } catch {}
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker Desktop ist bereit." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    Write-Host "Docker Desktop antwortet nach $TimeoutSeconds Sekunden nicht - bitte manuell pruefen" -ForegroundColor Yellow
    return $false
}

Write-Host "=== A.R.I.A Start-Workflow ===" -ForegroundColor Cyan

if (-not (Wait-ForDockerDesktop)) {
    Write-Host "Abbruch: Docker Desktop ist nicht bereit gekommen." -ForegroundColor Red
    exit 1
}
Set-Location $root
Write-Host "Starte Docker-Dienste (llm/stt/tts)..." -ForegroundColor Cyan
docker compose up -d

Wait-ForHealth -Url "http://localhost:11434/" -Name "Ollama (LLM)"
Wait-ForHealth -Url "http://localhost:8001/health" -Name "STT"
Wait-ForHealth -Url "http://localhost:8002/health" -Name "TTS"

$venvPython = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Starte Orchestrator in eigenem Fenster..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\orchestrator'; & '$venvPython' -m uvicorn main:app --reload --port 8000"
)

Wait-ForHealth -Url "http://localhost:8000/health" -Name "Orchestrator"

Write-Host "Starte Frontend-Dev-Server in eigenem Fenster..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "Warte kurz, bis Vite hochgefahren ist..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

Write-Host "Oeffne Browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "=== A.R.I.A ist online ===" -ForegroundColor Green
