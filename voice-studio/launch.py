"""Portable foreground launcher for Alibi."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / (".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python")
PID_FILE = ROOT / "logs/voice-studio-processes.json"


def healthy() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=2) as response:
            return json.loads(response.read()).get("status") == "ready"
    except Exception:
        return False


def main() -> None:
    if not PYTHON.exists():
        raise SystemExit("Missing .venv. Run install.py first.")
    if healthy():
        webbrowser.open("http://127.0.0.1:8765")
        return
    (ROOT / "logs").mkdir(exist_ok=True)
    processes = []
    for name, port in (("inference", 8766), ("backend", 8765)):
        log = (ROOT / "logs" / f"{name}.log").open("a", encoding="utf-8")
        process = subprocess.Popen([str(PYTHON), "scripts/run_server.py", name], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        log.close()
        processes.append({"name": name, "pid": process.pid, "port": port})
    PID_FILE.write_text(json.dumps(processes, indent=2), encoding="utf-8")
    for _ in range(60):
        if healthy():
            webbrowser.open("http://127.0.0.1:8765")
            print("Alibi: http://127.0.0.1:8765")
            return
        time.sleep(1)
    raise SystemExit("Studio did not become ready. Inspect logs/backend.log.")


if __name__ == "__main__":
    main()
