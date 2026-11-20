import os
import sys
import webbrowser
import time
import threading
import uvicorn

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("[*] Starting DrapeAI: AI Virtual Stylist & Try-On System...")
    print("[*] URL: http://127.0.0.1:8000")
    print("[*] Working Directory:", os.path.abspath("."))
    print("=" * 60)

    # Launch browser automatically
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI server
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
