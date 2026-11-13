"""One-click Windows installer for Alibi.

The PyInstaller build embeds the application and its production frontend. The
installer downloads only machine-specific runtime pieces and model weights.
"""
from __future__ import annotations

import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile


APP_NAME = "Alibi"
PYTHON_VERSION = "3.12.10"
PYTHON_INSTALLER_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
BASE_REPOS = ["Qwen/Qwen3-TTS-12Hz-1.7B-Base", "Qwen/Qwen3-TTS-Tokenizer-12Hz"]
VOICE_DESIGN_REPO = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"


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


def python_install(python_installer: Path, target: Path, log) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        str(python_installer), "/quiet", "InstallAllUsers=0", "Include_pip=1",
        "PrependPath=0", "Include_test=0", f"TargetDir={target}",
    ], check=True)
    python = target / "python.exe"
    if not python.exists():
        raise RuntimeError("Python installation completed but python.exe was not found.")
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


def create_shortcut(path: Path, target: Path, arguments: str, working_directory: Path) -> None:
    def quote(value: str) -> str:
        return value.replace("'", "''")
    script = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{path}');"
        "$s.TargetPath='{target}';$s.Arguments='{arguments}';"
        "$s.WorkingDirectory='{working}';$s.Description='Alibi';$s.Save()"
    ).format(path=quote(str(path)), target=quote(str(target)), arguments=quote(arguments), working=quote(str(working_directory)))
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], check=True)


def register_uninstall(uninstall_command: str, install_dir: Path) -> None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Alibi"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Alibi")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_command)


def install(voice_design: bool, log, progress) -> None:
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
        python_installer = temp / "python.exe"
        log("Downloading Python 3.12 runtime...")
        download(PYTHON_INSTALLER_URL, python_installer, progress)
        python = python_install(python_installer, runtime_dir, log)
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
    create_shortcut(start_menu / "Alibi.lnk", start_script, "", root)
    if desktop.exists():
        create_shortcut(desktop / "Alibi.lnk", start_script, "", root)
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
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.voice_design = tk.BooleanVar(value=False)
        ttk.Label(self.root, text="Alibi", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=30, pady=(24, 2))
        ttk.Label(self.root, text="One-click local voice workspace installer", font=("Segoe UI", 10)).pack(anchor="w", padx=32)
        ttk.Checkbutton(self.root, text="Install VoiceDesign model too (adds about 4.2 GB)", variable=self.voice_design).pack(anchor="w", padx=32, pady=18)
        self.status = ttk.Label(self.root, text="Ready to install")
        self.status.pack(anchor="w", padx=32)
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=32, pady=(8, 12))
        button_row = ttk.Frame(self.root)
        button_row.pack(fill="x", padx=32, pady=(0, 10))
        self.button = ttk.Button(button_row, text="Install Alibi", command=self.start, takefocus=True)
        self.button.pack(side="right")
        ttk.Label(button_row, text="Press Enter to start", foreground="#555555").pack(side="left")
        log_frame = ttk.LabelFrame(self.root, text="Installation log")
        log_frame.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        self.log_text = tk.Text(log_frame, height=log_height(), width=86, state="disabled", wrap="word",
                                background="#ffffff", foreground="#202020", insertbackground="#202020",
                                takefocus=True, relief="solid", borderwidth=1)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.root.bind("<Return>", lambda _event: self.start() if str(self.button["state"]) == "normal" else None)
        self.root.after(250, self.button.focus_set)
        self.root.after(100, self.poll)

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
        threading.Thread(target=self.worker, args=(voice_design,), daemon=True).start()

    def worker(self, voice_design: bool) -> None:
        try:
            install(voice_design, self.write_log, lambda done, total: self.events.put(("progress", (done, total))))
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
