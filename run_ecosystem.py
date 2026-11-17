import os
import sys
import subprocess
import time
import webbrowser

SERVICES = [
    {"name": "Auth Service (FastAPI + JWT)", "dir": "services/auth_service", "port": 8001},
    {"name": "Advisory Service (Module 1 & 2)", "dir": "services/advisory_service", "port": 8002},
    {"name": "Marketplace Service (Redis + Catalog)", "dir": "services/marketplace_service", "port": 8003},
    {"name": "Recommendation ML Service", "dir": "services/recommendation_service", "port": 8004},
    {"name": "Analytics ML Service", "dir": "services/analytics_service", "port": 8005},
    {"name": "Personal Budget Service (VaultAI ReAct)", "dir": "services/personal_budget_service", "port": 8006},
]

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    processes = []

    print("=" * 76)
    print("🌾 GRAMINUDYAM AI & VAULTAI: UNIFIED RURAL & PERSONAL BUDGET ECOSYSTEM")
    print("=" * 76)

    # Launch all 6 microservices
    for svc in SERVICES:
        svc_dir = os.path.join(root_dir, svc["dir"])
        print(f"🚀 Starting {svc['name']} on http://localhost:{svc['port']} ...")
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(svc["port"])]
        p = subprocess.Popen(cmd, cwd=svc_dir)
        processes.append(p)
        time.sleep(1)

    # Launch Frontend Static Web Server
    frontend_dir = os.path.join(root_dir, "frontend")
    print("🌐 Starting React Frontend on http://localhost:3000 ...")
    cmd_frontend = [sys.executable, "-m", "http.server", "3000"]
    p_front = subprocess.Popen(cmd_frontend, cwd=frontend_dir)
    processes.append(p_front)

    time.sleep(2)
    print("\n" + "=" * 76)
    print("✅ All 6 Microservices and React UI are live!")
    print("🔗 Unified Platform: http://localhost:3000")
    print("   • Entrepreneur / Beneficiary Portal (Schemes & Feasibility)")
    print("   • Personal Budget Assistant Portal (VaultAI ReAct Copilot)")
    print("   • Seller / Equipment Supplier Portal (Inventory & ML Forecasts)")
    print("=" * 76)
    print("\nPress Ctrl+C to stop all services.\n")

    webbrowser.open("http://localhost:3000")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all microservices...")
        for p in processes:
            p.terminate()
        print("All services stopped.")

if __name__ == "__main__":
    main()
