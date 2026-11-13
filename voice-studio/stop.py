"""Portable launcher cleanup for Alibi."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal


ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / "logs/voice-studio-processes.json"


def main() -> None:
    if not PID_FILE.exists():
        print("Alibi is not running.")
        return
    for item in json.loads(PID_FILE.read_text(encoding="utf-8")):
        try:
            os.kill(item["pid"], signal.SIGTERM)
            print("Stopped", item["name"])
        except ProcessLookupError:
            pass
    PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
