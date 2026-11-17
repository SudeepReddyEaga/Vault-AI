# ==============================================================================
# VAULT AI - 1-CLICK GIT PUSH, JENKINS BUILD & AUTOMATIC BROWSER LAUNCHER
# ==============================================================================

param (
    [string]$CommitMessage = "Update microservices and DevOps configs",
    [switch]$SkipGitPush = $false
)

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 VAULT AI - AUTOMATED GIT PUSH & JENKINS PERSONAL PC WORKFLOW" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Start Windows Host Browser Bridge in Background (if not running)
$bridgeRunning = $false
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8765/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
    if ($resp.status -eq "ok") {
        $bridgeRunning = $true
        Write-Host "🟢 Windows Host Browser Bridge already running on Port 8765." -ForegroundColor Green
    }
} catch {
    $bridgeRunning = $false
}

if (-not $bridgeRunning) {
    Write-Host "⚡ Starting Windows Host Browser Bridge on Port 8765..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "scripts/windows_browser_bridge.py" -WindowStyle Hidden
    Start-Sleep -Seconds 1
}

# 2. Push to GitHub (Optional or Prompted)
if (-not $SkipGitPush) {
    Write-Host "`n📦 Stage 1: Pushing changes to GitHub..." -ForegroundColor Yellow
    git status --short
    $gitRemote = git remote -v
    if ($gitRemote) {
        Write-Host "Pushing to remote origin main..." -ForegroundColor Gray
        git add .
        git commit -m $CommitMessage 2>$null
        git push origin main
        Write-Host "✅ Git changes pushed to GitHub successfully!" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ No git remote configured. Continuing to local build..." -ForegroundColor Cyan
    }
}

# 3. Check Jenkins Container Health
Write-Host "`n🔍 Stage 2: Checking Jenkins Master on Port 8080..." -ForegroundColor Yellow
try {
    $jResp = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 3
    Write-Host "🟢 Jenkins Master is UP and accessible at http://localhost:8080" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Jenkins Master is initializing or not responding at port 8080." -ForegroundColor Red
}

# 4. Trigger / Execute Local Pipeline Stages
Write-Host "`n🐳 Stage 3: Running Docker Build & DevSecOps Pipeline..." -ForegroundColor Yellow
python scripts/run_devsecops_pipeline.py

# 5. Launch all Service Web Pages in Browser
Write-Host "`n🌐 Stage 4: Launching all Service Web Pages in your default browser..." -ForegroundColor Yellow
python scripts/open_browser_pages.py

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host "✅ WORKFLOW COMPLETE: All services built, deployed, and web pages opened!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
