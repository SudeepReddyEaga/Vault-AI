#!/usr/bin/env python3
"""
VAULT AI - WINDOWS HOST BROWSER BRIDGE (PORT 8765)
Runs as a lightweight background service on the developer's personal PC.
Listens for deployment notifications from Jenkins (or any container via http://host.docker.internal:8765/open)
and automatically launches all service web interfaces in the Windows default browser.
"""

import sys
import time
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

BRIDGE_PORT = 8765

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

def launch_browser_tabs(delay: float = 0.4):
    print("\n🚀 [Browser Bridge] Opening service web pages on Windows Host...")
    for s in SERVICES:
        print(f"  • Launching {s['name']} -> {s['url']}")
        try:
            webbrowser.open_new_tab(s["url"])
            time.sleep(delay)
        except Exception as e:
            print(f"    ⚠️ Failed to open {s['url']}: {e}")
    print("✅ [Browser Bridge] All web pages opened on host desktop!\n")

class BridgeRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path in ["/open", "/open/"]:
            launch_browser_tabs()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "All service tabs opened in Windows browser."}).encode("utf-8"))
        elif self.path in ["/health", "/health/"]:
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "windows-browser-bridge", "port": BRIDGE_PORT}).encode("utf-8"))
        else:
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"VaultAI Windows Browser Bridge running on port 8765. Call POST /open to launch tabs.")

    def do_POST(self):
        if self.path in ["/open", "/open/"]:
            launch_browser_tabs()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "All service tabs opened in Windows browser."}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Concise logging
        sys.stdout.write(f"[Bridge HTTP] {args[0]} - {args[1]}\n")
        sys.stdout.flush()

def main():
    print("=" * 72)
    print(f"🌐 VAULT AI - WINDOWS HOST BROWSER BRIDGE LISTENER (PORT {BRIDGE_PORT})")
    print("=" * 72)
    print(f"Listening on http://0.0.0.0:{BRIDGE_PORT}")
    print("Jenkins inside Docker can notify: http://host.docker.internal:8765/open")
    print("Host PC processes can notify:      http://localhost:8765/open")
    print("Press Ctrl+C to terminate.")
    print("=" * 72)
    sys.stdout.flush()

    server = HTTPServer(("0.0.0.0", BRIDGE_PORT), BridgeRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Windows Browser Bridge.")
        server.server_close()

if __name__ == "__main__":
    main()
