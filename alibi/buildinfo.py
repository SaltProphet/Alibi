"""Resolve which Alibi version and build is running.

``version.json`` in the repository root is the single hand-edited source of the
version number. A real build also writes ``build-info.json`` beside this module
so an installed copy, which has no Git history, can still report version,
commit, and build time. A source checkout reports its live Git state instead,
which keeps the answer correct immediately after a commit.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent


def _version_from(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("version")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def build_info(root: Path | None = None) -> dict:
    """Return version, commit, dirty, built_at, and source for an app copy."""
    app = Path(root or APP_ROOT).resolve()
    repo = app.parent
    version = _version_from(repo / "version.json") or _version_from(app / "version.json")

    if (repo / ".git").exists():
        # A checkout can answer for itself, so a leftover build stamp cannot lie.
        return {
            "version": version or "0.0.0-dev",
            "commit": _git(repo, "rev-parse", "HEAD") or "unknown",
            "dirty": bool(_git(repo, "status", "--porcelain")),
            "built_at": "",
            "source": "source",
        }

    try:
        stamp = json.loads((app / "build-info.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stamp = None
    if isinstance(stamp, dict) and isinstance(stamp.get("version"), str) and stamp["version"].strip():
        return {
            "version": stamp["version"].strip(),
            "commit": str(stamp.get("commit") or "unknown"),
            "dirty": bool(stamp.get("dirty")),
            "built_at": str(stamp.get("built_at") or ""),
            "source": "build",
        }

    return {
        "version": version or "0.0.0-dev",
        "commit": "unknown",
        "dirty": False,
        "built_at": "",
        "source": "unknown",
    }
