# ==============================================================================
# SIH26001: AI-Based Early Warning & Landslide Risk Monitoring System
# Multi-Platform Launch Orchestrator (Windows PowerShell)
# ==============================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  SIH26001: North Eastern Region Landslide Early Warning System       " -ForegroundColor Yellow
Write-Host "  Starting Backend (FastAPI :8000) & Frontend (Next.js :3000)         " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Start Backend in background process
Write-Host "`n[1/3] Starting Disaster Intelligence Engine Backend (Port 8000)..." -ForegroundColor Green
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

# 2. Wait for backend health
Write-Host "[2/3] Verifying Backend Health..." -ForegroundColor Yellow
Start-Sleep -Seconds 4
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host ">> Backend Online! Service: $($health.service) | Version: $($health.version)" -ForegroundColor Green
} catch {
    Write-Host ">> Backend is initializing..." -ForegroundColor Yellow
}

# 3. Start Frontend in background process
Write-Host "[3/3] Starting Command Center & Public Portal Frontend (Port 3000)..." -ForegroundColor Green
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  SYSTEM ACCESS URLS:                                                 " -ForegroundColor Yellow
Write-Host "  - Core Expert Command Center:   http://localhost:3000               " -ForegroundColor White
Write-Host "  - Field Rescue Operations:      http://localhost:3000/field         " -ForegroundColor White
Write-Host "  - Public Safety Portal:         http://localhost:3000/public        " -ForegroundColor White
Write-Host "  - Model Calibration Studio:     http://localhost:3000/analytics     " -ForegroundColor White
Write-Host "  - CAP v1.2 XML Feed:            http://localhost:8000/api/v1/alerts/cap.xml" -ForegroundColor White
Write-Host "  - Interactive OpenAPI Docs:     http://localhost:8000/docs          " -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
