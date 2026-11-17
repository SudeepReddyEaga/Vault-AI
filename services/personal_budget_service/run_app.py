import os
import sys
import time
import webbrowser
import threading

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" Personal Budget Assistant - AI Agent Web Application")
    print("="*60)
    print(" Starting server on http://localhost:5000 ...")
    print(" Opening browser window...")
    print(" Press Ctrl+C in terminal to stop server.\n")

    threading.Thread(target=open_browser, daemon=True).start()

    from server import app
    app.run(host="0.0.0.0", port=5000, debug=False)

