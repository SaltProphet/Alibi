"""Portable foreground launcher for Alibi.

The studio binds to local ports, so another program can already own the
preferred ones. Pick free ports instead of failing, and remember them for the
run so the browser and the stop script agree.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / (".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python")
PID_FILE = ROOT / "logs/alibi-processes.json"
BACKEND_PORT = 8765
INFERENCE_PORT = 8766
PORT_SEARCH = 40


def health(port: int, timeout: float = 2) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as response:
            return json.loads(response.read())
    except Exception:
        return None


def port_available(port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def pick_port(preferred: int, blocked: set[int] | None = None) -> int:
    """Return the preferred port, or the next free one, skipping blocked ports."""
    blocked = blocked or set()
    for port in range(preferred, preferred + PORT_SEARCH):
        if port in blocked:
            continue
        if port_available(port):
            return port
    raise SystemExit(f"No free port found between {preferred} and {preferred + PORT_SEARCH - 1}.")


def running_alibi() -> int | None:
    """Find an Alibi instance already serving, wherever it landed."""
    for port in range(BACKEND_PORT, BACKEND_PORT + PORT_SEARCH):
        info = health(port, timeout=.4)
        if info and info.get("build"):
            return port
    return None


def main() -> None:
    if not PYTHON.exists():
        raise SystemExit("Missing .venv. Run install.py first.")
    existing = running_alibi()
    if existing:
        webbrowser.open(f"http://127.0.0.1:{existing}")
        return

    (ROOT / "logs").mkdir(exist_ok=True)
    blocked: set[int] = set()
    backend_port = pick_port(BACKEND_PORT, blocked)
    blocked.add(backend_port)
    inference_port = pick_port(INFERENCE_PORT, blocked)

    env = os.environ.copy()
    env["ALIBI_PORT"] = str(backend_port)
    env["ALIBI_INFERENCE_PORT"] = str(inference_port)
    env["ALIBI_WORKER_URL"] = f"http://127.0.0.1:{inference_port}"

    processes = []
    for name, port in (("inference", inference_port), ("backend", backend_port)):
        log = (ROOT / "logs" / f"{name}.log").open("a", encoding="utf-8")
        process = subprocess.Popen([str(PYTHON), "scripts/run_server.py", name], cwd=ROOT,
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
        log.close()
        processes.append({"name": name, "pid": process.pid, "port": port})
    PID_FILE.write_text(json.dumps(processes, indent=2), encoding="utf-8")

    url = f"http://127.0.0.1:{backend_port}"
    for _ in range(120):
        info = health(backend_port)
        if info and info.get("status") == "ready":
            webbrowser.open(url)
            print(f"Alibi: {url}")
            return
        time.sleep(1)
    raise SystemExit(f"Alibi did not become ready on port {backend_port}. Inspect logs/backend.log.")


if __name__ == "__main__":
    main()
