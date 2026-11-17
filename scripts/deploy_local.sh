#!/usr/bin/env bash
# =========================================================================
# VAULT AI - LOCAL DEVOPS ECOSYSTEM DEPLOYMENT SCRIPT (Linux / macOS)
# =========================================================================

set -e

echo "============================================================================"
echo "🚀 STARTING VAULT AI LOCAL DEVOPS ECOSYSTEM (WITHOUT AWS)"
echo "============================================================================"

# 1. DevSecOps Security Gates
echo -e "\n[Step 1/3] Running DevSecOps Security Gates..."
python3 scripts/run_devsecops_pipeline.py

# 2. Docker Compose
echo -e "\n[Step 2/3] Starting Docker Compose stack..."
if command -v docker >/dev/null 2>&1; then
    docker compose -f docker-compose.devops.yml up -d --build
else
    echo "Docker not available. Starting local python services..."
    python3 services/ml_forecast_engine/main.py &
    python3 services/ai_agent_copilot/main.py &
    python3 services/budget_api_service/main.py &
fi

# 3. Verification
echo -e "\n[Step 3/3] Verifying endpoints..."
sleep 3
python3 scripts/verify_ecosystem.py

echo "============================================================================"
echo "🎉 DEPLOYMENT COMPLETE! All local ports are accessible."
echo "============================================================================"
