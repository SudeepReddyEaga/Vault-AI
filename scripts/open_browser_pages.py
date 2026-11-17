#!/usr/bin/env python3
"""
VAULT AI - AUTOMATIC SERVICE BROWSER LAUNCHER
Opens all active service web interfaces in the user's default browser on their personal PC.
"""

import sys
import time
import webbrowser

SERVICES = [
    {"name": "Nginx Web Gateway (Port 80)", "url": "http://localhost:80"},
    {"name": "Grafana Telemetry Dashboard (Port 3000)", "url": "http://localhost:3000"},
    {"name": "Prometheus Telemetry Targets (Port 9090)", "url": "http://localhost:9090/targets"},
    {"name": "Budget API Swagger Docs (Port 5000)", "url": "http://localhost:5000/docs"},
    {"name": "AI Agent Copilot Swagger Docs (Port 5001)", "url": "http://localhost:5001/docs"},
    {"name": "ML Forecast Engine Swagger Docs (Port 5002)", "url": "http://localhost:5002/docs"},
    {"name": "HashiCorp Vault UI (Port 8200)", "url": "http://localhost:8200/ui"},
    {"name": "Jenkins Master CI/CD (Port 8080)", "url": "http://localhost:8080"}
]

def open_all(delay: float = 0.5):
    print("=" * 72)
    print("🌐 VAULT AI - LAUNCHING SERVICE WEB PAGES IN BROWSER")
    print("=" * 72)
    
    for s in SERVICES:
        print(f"  • Opening {s['name']:<42} -> {s['url']}")
        try:
            webbrowser.open_new_tab(s["url"])
            time.sleep(delay)
        except Exception as e:
            print(f"    ⚠️ Could not launch {s['url']}: {e}")
            
    print("=" * 72)
    print("✅ All service web pages launched successfully!")
    print("=" * 72)

if __name__ == "__main__":
    delay = 0.5
    if len(sys.argv) > 1:
        try:
            delay = float(sys.argv[1])
        except ValueError:
            pass
    open_all(delay)
