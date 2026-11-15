"""Portable launcher cleanup for Alibi."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / "logs/alibi-processes.json"


def terminate(pid: int) -> None:
    """Stop one process tree, tolerating processes that already exited."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return
    import signal
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def main() -> None:
    if not PID_FILE.exists():
        print("Alibi is not running.")
        return
    for item in json.loads(PID_FILE.read_text(encoding="utf-8")):
        terminate(item["pid"])
        print("Stopped", item["name"])
    PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
