"""Workspace settings, storage accounting, and diagnostics helpers.

Settings live in ``settings.json`` beside the user's data so they survive
reinstalls and travel with a workspace. Everything in this module is pure
enough to test without starting the API.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import time


SETTINGS_FILE = "settings.json"
LANGUAGES = [
    "English", "Chinese", "Japanese", "Korean", "French",
    "German", "Spanish", "Italian", "Portuguese", "Russian",
]
MODELS = {
    "Base": "Qwen3-TTS-12Hz-1.7B-Base",
    "VoiceDesign": "Qwen3-TTS-12Hz-1.7B-VoiceDesign",
}
DEFAULTS = {
    "default_language": "English",
    "preload_model": "",
    "idle_unload_minutes": 0,
    "reduce_motion": False,
    "compact_sidebar": False,
}
LIMITS = {
    "idle_unload_minutes": (0, 1440),
    "cleanup_days": (1, 3650),
}


def settings_path(data) -> Path:
    return Path(data) / SETTINGS_FILE


def _coerce(key: str, value):
    if key not in DEFAULTS:
        raise ValueError(f"Unknown setting: {key}")
    if key == "default_language":
        if value not in LANGUAGES:
            raise ValueError("Choose one of: " + ", ".join(LANGUAGES) + ".")
        return value
    if key == "preload_model":
        if value not in ("", *MODELS):
            raise ValueError("Choose no preload, Base, or VoiceDesign.")
        return value
    if key == "idle_unload_minutes":
        low, high = LIMITS[key]
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ValueError(f"Idle unload must be a whole number of minutes from {low} to {high}.")
        return value
    if key in ("reduce_motion", "compact_sidebar"):
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be true or false.")
        return value
    raise ValueError(f"Unknown setting: {key}")


def _stored(data) -> dict:
    try:
        value = json.loads(settings_path(data).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def read(data) -> dict:
    """Return every setting, falling back to defaults for missing or bad values."""
    stored = _stored(data)
    result = dict(DEFAULTS)
    for key in DEFAULTS:
        if key in stored:
            try:
                result[key] = _coerce(key, stored[key])
            except ValueError:
                continue
    return result


def write(data, patch: dict) -> dict:
    """Merge a validated patch into the stored settings and return the result."""
    if not isinstance(patch, dict):
        raise ValueError("Settings must be an object.")
    unknown = sorted(set(patch) - set(DEFAULTS))
    if unknown:
        raise ValueError(f"Unknown setting: {unknown[0]}")
    values = read(data)
    for key, value in patch.items():
        values[key] = _coerce(key, value)
    path = settings_path(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return values


def reset(data) -> dict:
    settings_path(data).unlink(missing_ok=True)
    return dict(DEFAULTS)


def directory_size(path) -> int:
    """Total bytes of the files under a directory, ignoring unreadable entries."""
    total = 0
    for root, _directories, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total


def storage_report(data, models) -> dict:
    data = Path(data)
    models = Path(models)
    return {
        "data": str(data),
        "models_path": str(models),
        "cache_path": str(models.parent / "cache"),
        "exports_path": str(data / "exports"),
        "recordings": directory_size(data / "audio") + directory_size(data / "originals"),
        "exports": directory_size(data / "exports"),
        "exports_count": len(list((data / "exports").glob("*.json"))),
        "data_total": directory_size(data),
        "models": directory_size(models),
        "cache": directory_size(models.parent / "cache"),
    }


def cleanup_exports(data, days: int) -> dict:
    """Delete exported mixes older than ``days`` and report what was removed."""
    low, high = LIMITS["cleanup_days"]
    if isinstance(days, bool) or not isinstance(days, int) or not low <= days <= high:
        raise ValueError(f"Choose a number of days from {low} to {high}.")
    cutoff = time.time() - days * 86400
    removed = freed = 0
    for meta in (Path(data) / "exports").glob("*.json"):
        try:
            if meta.stat().st_mtime >= cutoff:
                continue
        except OSError:
            continue
        audio = meta.with_suffix(".wav")
        try:
            freed += meta.stat().st_size
        except OSError:
            pass
        try:
            freed += audio.stat().st_size
        except OSError:
            pass
        meta.unlink(missing_ok=True)
        audio.unlink(missing_ok=True)
        removed += 1
    return {"removed": removed, "freed": freed}


def should_unload(now: float, last_used: float | None, minutes: int) -> bool:
    """True when a loaded model has been idle for the configured period."""
    if minutes <= 0 or not last_used:
        return False
    return now - last_used >= minutes * 60


def tail(path, lines: int = 120, max_bytes: int = 200_000) -> str:
    """Return the last ``lines`` lines of a log file without reading all of it."""
    target = Path(path)
    try:
        size = target.stat().st_size
        with target.open("rb") as handle:
            handle.seek(max(0, size - max_bytes))
            chunk = handle.read()
    except OSError:
        return ""
    text = chunk.decode("utf-8", "replace")
    return "\n".join(text.splitlines()[-lines:])
