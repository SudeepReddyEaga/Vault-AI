# =========================================================================
# VAULT AI - LOCAL DEVOPS ECOSYSTEM DEPLOYMENT SCRIPT (PowerShell)
# Runs without AWS: Starts Docker Compose with all 11 services and exact ports:
# 80/443 (HTTP/HTTPS), 5000 (Budget API), 5001 (AI Copilot), 5002 (ML Engine),
# 5432 (Postgres), 6379 (Redis), 8080 (Jenkins), 8200 (Vault), 9090 (Prometheus), 3000 (Grafana)
# =========================================================================

$ErrorActionPreference = "Continue"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING VAULT AI LOCAL DEVOPS ECOSYSTEM (WITHOUT AWS)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# 1. Run DevSecOps Pre-Deployment Security Gates
Write-Host "`n[Step 1/3] Running DevSecOps Security Gates (Flake8, Pytest, Bandit)..." -ForegroundColor Yellow
python scripts/run_devsecops_pipeline.py

# 2. Check Docker
Write-Host "`n[Step 2/3] Checking Docker daemon status..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($dockerVersion) {
    Write-Host "✅ Docker is active: $dockerVersion" -ForegroundColor Green
    Write-Host "Spinning up all 11 microservices via Docker Compose..." -ForegroundColor Yellow
    docker compose -f docker-compose.devops.yml up -d --build
} else {
    Write-Host "⚠️ Docker Desktop daemon is not running on this machine." -ForegroundColor Red
    Write-Host "Falling back to native Python concurrent execution of core services..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "services/ml_forecast_engine/main.py" -WindowStyle Minimized
    Start-Process -FilePath "python" -ArgumentList "services/ai_agent_copilot/main.py" -WindowStyle Minimized
    Start-Process -FilePath "python" -ArgumentList "services/budget_api_service/main.py" -WindowStyle Minimized
}

# 3. Verify Ecosystem Status
Write-Host "`n[Step 3/3] Verifying enterprise port bindings & health..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
python scripts/verify_ecosystem.py

Write-Host "`n============================================================================" -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT COMPLETE! Access endpoints:" -ForegroundColor Green
Write-Host "• Web Application / Gateway: http://localhost:80 or http://localhost:5000" -ForegroundColor White
Write-Host "• Grafana Monitoring:        http://localhost:3000 (admin / admin)" -ForegroundColor White
Write-Host "• Prometheus Metrics:        http://localhost:9090" -ForegroundColor White
Write-Host "• Jenkins CI/CD Automation:  http://localhost:8080" -ForegroundColor White
Write-Host "• HashiCorp Vault:           http://localhost:8200" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Green
