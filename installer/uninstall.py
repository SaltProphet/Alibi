"""Per-user Alibi uninstaller."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def main() -> None:
    if not messagebox.askyesno("Uninstall Alibi", "Remove Alibi but keep your recordings and models?"):
        return
    app = ROOT / "app"
    runtime = ROOT / "runtime"
    tools = ROOT / "tools"
    for path in (app, runtime, tools):
        shutil.rmtree(path, ignore_errors=True)
    for shortcut in (
        Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "Alibi.lnk",
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Alibi.lnk",
    ):
        shortcut.unlink(missing_ok=True)
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Alibi")
    except (FileNotFoundError, OSError):
        pass
    if messagebox.askyesno("Delete local data?", "Also delete recordings, profiles, sessions, exports, and downloaded models?"):
        shutil.rmtree(DATA, ignore_errors=True)
    messagebox.showinfo("Alibi", "Uninstallation complete.")
    shutil.rmtree(ROOT, ignore_errors=True)


if __name__ == "__main__":
    root = tk.Tk(); root.withdraw()
    main(); root.destroy()
