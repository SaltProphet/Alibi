"""One-click Windows installer for Alibi.

The PyInstaller build embeds the application and its production frontend. The
installer downloads only machine-specific runtime pieces and model weights.
"""
from __future__ import annotations

import os
from pathlib import Path
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile


APP_NAME = "Alibi"
ICON_NAME = "Alibi.ico"
PYTHON_VERSION = "3.12.10"
PYTHON_RUNTIME_URL = f"https://www.nuget.org/api/v2/package/python/{PYTHON_VERSION}"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
BASE_REPOS = ["Qwen/Qwen3-TTS-12Hz-1.7B-Base", "Qwen/Qwen3-TTS-Tokenizer-12Hz"]
VOICE_DESIGN_REPO = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
COLORS = {
    "ink": "#171310",
    "brown": "#2a201b",
    "cream": "#f1e8d2",
    "orange": "#e75b2c",
    "muted": "#b9aa92",
}


def visual_tagline() -> str:
    return "Runs locally. No account required."


def window_geometry() -> str:
    return "760x620"


def log_height() -> int:
    return 9


def install_directory(local_appdata: str | os.PathLike[str]) -> Path:
    return Path(local_appdata) / "Alibi"


def model_repos(*, voice_design: bool) -> list[str]:
    return [*BASE_REPOS, *( [VOICE_DESIGN_REPO] if voice_design else [])]


def minimum_free_bytes(voice_design: bool) -> int:
    return (24 if voice_design else 20) * 1024**3


def payload_root() -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / "payload"


def download(url: str, destination: Path, progress) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AlibiSetup/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        total = int(response.headers.get("Content-Length", "0"))
        completed = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
            completed += len(chunk)
            progress(completed, total)


def run_logged(args: list[str], *, cwd: Path, env: dict[str, str], log) -> None:
    log("$ " + " ".join(args))
    process = subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, errors="replace")
    assert process.stdout is not None
    for line in process.stdout:
        log(line.rstrip())
    if process.wait() != 0:
        raise RuntimeError(f"Command failed with exit code {process.returncode}: {args[0]}")


def python_install(runtime_package: Path, target: Path, log) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    log("Extracting bundled Python runtime...")
    with zipfile.ZipFile(runtime_package) as bundle:
        members = [member for member in bundle.namelist() if member.startswith("tools/")]
        if not members:
            raise RuntimeError("Python runtime package did not contain its tools directory.")
        for member in members:
            relative = Path(member.removeprefix("tools/"))
            if not relative.parts:
                continue
            destination = target / relative
            if member.endswith("/"):
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
    python = target / "python.exe"
    if not python.exists():
        raise RuntimeError(f"Python runtime extraction completed but python.exe was not found in {target}.")
    log(f"Installed Python {PYTHON_VERSION}.")
    return python


def extract_ffmpeg(archive: Path, target: Path, log) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(target)
    candidates = list(target.rglob("ffmpeg.exe"))
    if not candidates:
        raise RuntimeError("Downloaded FFmpeg archive did not contain ffmpeg.exe.")
    ffmpeg_dir = candidates[0].parent
    log(f"Installed FFmpeg from {ffmpeg_dir}.")
    return ffmpeg_dir


def create_shortcut(path: Path, target: Path, arguments: str, working_directory: Path, icon: Path | None = None) -> None:
    def quote(value: str) -> str:
        return value.replace("'", "''")
    script = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{path}');"
        "$s.TargetPath='{target}';$s.Arguments='{arguments}';"
        "$s.WorkingDirectory='{working}';$s.Description='Alibi';"
        "$s.IconLocation='{icon}';$s.Save()"
    ).format(path=quote(str(path)), target=quote(str(target)), arguments=quote(arguments), working=quote(str(working_directory)), icon=quote(shortcut_icon_argument(icon.parent) if icon else ""))
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], check=True)


def shortcut_icon_argument(install_root: Path) -> str:
    return f"{install_root / ICON_NAME},0"


def shortcut_targets(create_desktop: bool, start_menu: Path, desktop: Path | None) -> list[Path]:
    targets = [start_menu / "Alibi.lnk"]
    if create_desktop and desktop is not None:
        targets.append(desktop / "Alibi.lnk")
    return targets


def register_uninstall(uninstall_command: str, install_dir: Path) -> None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Alibi"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Alibi")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_command)


def install(voice_design: bool, log, progress, create_desktop_shortcut: bool = True) -> None:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        raise RuntimeError("LOCALAPPDATA is unavailable; this installer requires Windows per-user storage.")
    root = install_directory(local_appdata)
    usage = shutil.disk_usage(root.parent)
    if usage.free < minimum_free_bytes(voice_design):
        raise RuntimeError(f"At least {minimum_free_bytes(voice_design) // 1024**3} GB of free space is required.")

    app_dir = root / "app"
    runtime_dir = root / "runtime"
    tools_dir = root / "tools"
    payload = payload_root()
    source_app = payload / "voice-studio"
    if not source_app.exists():
        raise RuntimeError("Installer payload is incomplete: voice-studio was not found.")
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_app, app_dir, dirs_exist_ok=True)
    log(f"Installed application files to {app_dir}.")

    with tempfile.TemporaryDirectory(prefix="alibi-setup-") as temporary:
        temp = Path(temporary)
        python_package = temp / "python.nupkg"
        log("Downloading Python 3.12 runtime...")
        download(PYTHON_RUNTIME_URL, python_package, progress)
        python = python_install(python_package, runtime_dir, log)
        ffmpeg_archive = temp / "ffmpeg.zip"
        log("Downloading FFmpeg...")
        download(FFMPEG_URL, ffmpeg_archive, progress)
        ffmpeg_dir = extract_ffmpeg(ffmpeg_archive, tools_dir, log)
        env = os.environ.copy()
        env["PATH"] = str(ffmpeg_dir) + os.pathsep + env.get("PATH", "")
        env["VOICE_STUDIO_DATA"] = str(root / "data")
        args = [str(python), "install.py", "--bundled"]
        if voice_design:
            args.append("--voice-design")
        run_logged(args, cwd=app_dir, env=env, log=log)

    uninstall_source = payload / "installer" / "uninstall.py"
    uninstaller = root / "Uninstall.exe"
    if uninstall_source.exists():
        shutil.copy2(uninstall_source, root / "uninstall.py")
    else:
        raise RuntimeError("Installer payload is incomplete: uninstall script was not found.")
    start_script = root / "Launch-Alibi.cmd"
    start_script.write_text(f'@echo off\n"{runtime_dir / "python.exe"}" "{app_dir / "launch.py"}"\n', encoding="utf-8")
    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    start_menu.mkdir(parents=True, exist_ok=True)
    icon = root / ICON_NAME
    icon_source = payload / "installer" / ICON_NAME
    if not icon_source.exists():
        raise RuntimeError("Installer payload is incomplete: shortcut icon was not found.")
    shutil.copy2(icon_source, icon)
    for shortcut in shortcut_targets(create_desktop_shortcut, start_menu, desktop if desktop.exists() else None):
        create_shortcut(shortcut, start_script, "", root, icon)
    register_uninstall(f'"{runtime_dir / "python.exe"}" "{root / "uninstall.py"}"', root)
    log("Created Start Menu and Desktop shortcuts.")
    progress(1, 1)


class InstallerWindow:
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk
        self.tk = tk
        self.root = tk.Tk()
        self.root.title("Alibi Setup")
        self.root.geometry(window_geometry())
        self.root.minsize(700, 560)
        self.root.resizable(True, True)
        self.root.configure(background=COLORS["ink"])
        style = ttk.Style(self.root)
        style.configure("Card.TFrame", background=COLORS["ink"])
        style.configure("Card.TLabel", background=COLORS["ink"], foreground=COLORS["cream"], font=("Segoe UI", 10))
        style.configure("Muted.Card.TLabel", background=COLORS["ink"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Card.TCheckbutton", background=COLORS["ink"], foreground=COLORS["cream"], font=("Segoe UI", 10))
        style.map("Card.TCheckbutton", background=[("active", COLORS["ink"])])
        style.configure("Orange.TButton", background=COLORS["orange"], foreground="#ffffff", padding=(18, 8), font=("Segoe UI", 10, "bold"))
        style.map("Orange.TButton", background=[("active", "#f27647"), ("disabled", "#9a7664")])
        style.configure("Card.Horizontal.TProgressbar", troughcolor=COLORS["brown"], background=COLORS["orange"], lightcolor=COLORS["orange"], darkcolor=COLORS["orange"])
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.voice_design = tk.BooleanVar(value=False)
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.hero = tk.Canvas(self.root, height=250, background=COLORS["ink"], highlightthickness=0)
        self.hero.pack(fill="x")
        self.hero.bind("<Configure>", self.draw_hero)
        self.draw_hero()
        card = ttk.Frame(self.root, style="Card.TFrame", padding=(34, 14, 34, 20))
        card.pack(fill="both", expand=True, padx=0, pady=(0, 0))
        ttk.Label(card, text="INSTALL ALIBI", style="Muted.Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(card, text="A private voice workspace, installed on this PC.", style="Card.TLabel", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(3, 2))
        ttk.Label(card, text="Base model and tokenizer are included. VoiceDesign is optional.", style="Muted.Card.TLabel").pack(anchor="w")
        ttk.Checkbutton(card, text="Add VoiceDesign model (about 4.2 GB extra)", variable=self.voice_design, style="Card.TCheckbutton").pack(anchor="w", pady=(13, 8))
        ttk.Checkbutton(card, text="Create a desktop shortcut", variable=self.create_desktop_shortcut, style="Card.TCheckbutton").pack(anchor="w", pady=(0, 8))
        self.status = ttk.Label(card, text="Ready to install", style="Card.TLabel")
        self.status.pack(anchor="w")
        self.progress = ttk.Progressbar(card, mode="indeterminate", style="Card.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(7, 9))
        button_row = ttk.Frame(card, style="Card.TFrame")
        button_row.pack(fill="x", pady=(0, 8))
        self.button = tk.Button(
            button_row, text="Install Alibi", command=self.start, takefocus=True,
            background=COLORS["orange"], foreground="#ffffff",
            activebackground="#f27647", activeforeground="#ffffff",
            disabledforeground="#ead8cb", relief="flat", borderwidth=0,
            padx=18, pady=8, font=("Segoe UI", 10, "bold"), cursor="hand2",
        )
        self.button.pack(side="right")
        ttk.Label(button_row, text="Tab to navigate · Enter to install", style="Muted.Card.TLabel").pack(side="left")
        log_frame = tk.Frame(card, background=COLORS["brown"], highlightbackground=COLORS["orange"], highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=log_height(), width=86, state="disabled", wrap="word",
                                background=COLORS["brown"], foreground=COLORS["cream"], insertbackground=COLORS["cream"],
                                takefocus=True, relief="solid", borderwidth=1)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.root.bind("<Return>", lambda _event: self.start() if str(self.button["state"]) == "normal" else None)
        self.root.after(250, self.button.focus_set)
        self.root.after(100, self.poll)

    def draw_hero(self, _event=None) -> None:
        width = max(self.hero.winfo_width(), 760)
        self.hero.delete("all")
        self.hero.create_rectangle(0, 0, width, 250, fill=COLORS["ink"], outline="")
        rng = random.Random(17)
        for _ in range(240):
            x = rng.randrange(width)
            y = rng.randrange(250)
            size = rng.choice((1, 1, 1, 2, 3))
            tint = rng.choice(("#221a16", "#30231d", "#3a2a22", "#1d1714"))
            self.hero.create_oval(x, y, x + size, y + size, fill=tint, outline="")
        for y in (18, 47, 79, 111, 146, 183, 221):
            self.hero.create_line(0, y, width, y + rng.choice((-2, -1, 0, 1, 2)), fill="#241a16", width=1)
        self.hero.create_text(32, 25, text="ALIBI", anchor="nw", fill=COLORS["cream"], font=("Georgia", 64, "bold"))
        self.hero.create_rectangle(34, 116, max(260, width - 34), 124, fill=COLORS["orange"], outline="")
        self.hero.create_text(34, 139, text=visual_tagline(), anchor="nw", fill=COLORS["cream"], font=("Georgia", 17, "bold"))
        self.hero.create_text(34, 211, text="SALT PROPHET  /  ALIBI", anchor="nw", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))

    def write_log(self, text: str) -> None:
        self.events.put(("log", text))

    def start(self) -> None:
        if str(self.button["state"]) != "normal" or self.button["text"] == "Close":
            return
        self.button.configure(state="disabled")
        self.status.configure(text="Preparing installation…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        voice_design = bool(self.voice_design.get())
        create_desktop_shortcut = bool(self.create_desktop_shortcut.get())
        threading.Thread(target=self.worker, args=(voice_design, create_desktop_shortcut), daemon=True).start()

    def worker(self, voice_design: bool, create_desktop_shortcut: bool) -> None:
        try:
            install(voice_design, self.write_log, lambda done, total: self.events.put(("progress", (done, total))), create_desktop_shortcut)
            self.events.put(("done", None))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", str(value) + "\n")
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
                elif kind == "progress":
                    done, total = value
                    if total:
                        self.progress.stop()
                        self.progress.configure(mode="determinate", maximum=total, value=done)
                        self.status.configure(text=f"Downloading… {done // 1024**2} / {total // 1024**2} MB")
                elif kind == "done":
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=100)
                    self.status.configure(text="Installation complete. Launch Alibi from the shortcut.")
                    self.button.configure(text="Close", state="normal", command=self.root.destroy)
                elif kind == "error":
                    self.progress.stop()
                    self.status.configure(text="Installation failed")
                    self.write_log("ERROR: " + str(value))
                    self.button.configure(text="Try again", state="normal", command=self.start)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    InstallerWindow().run()
