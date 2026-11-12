"""Cross-platform Voice Studio installer.

This script installs the project into a local .venv and never writes outside
the repository except for the package-manager caches used by Python and npm.
Use --skip-models for an offline/source-only setup.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
CUDA_TORCH_INDEX = "https://download.pytorch.org/whl/cu128"
CPU_TORCH_INDEX = "https://download.pytorch.org/whl/cpu"
QWEN_REVISION = "022e286b98fbec7e1e916cb940cdf532cd9f488e"


def requirements_without_torch(text: str) -> str:
    return "".join(line for line in text.splitlines(keepends=True)
                    if not line.lstrip().lower().startswith(("torch==", "torchaudio==", "torchvision==")))


def torch_install_args(cuda: bool) -> list[str]:
    return ["--index-url", CUDA_TORCH_INDEX if cuda else CPU_TORCH_INDEX]


def platform_summary(cuda: bool) -> str:
    accelerator = "CUDA/NVIDIA" if cuda else "CPU"
    return f"{platform.system()} {platform.machine()} · {accelerator} mode"


def command(name: str) -> str | None:
    return shutil.which(name)


def run(args: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def has_cuda() -> bool:
    if os.environ.get("VOICE_STUDIO_CPU", "").lower() in {"1", "true", "yes"}:
        return False
    nvidia = command("nvidia-smi")
    if not nvidia:
        return False
    return subprocess.run([nvidia, "-L"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def python_in_venv() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def check_prerequisites() -> None:
    missing = [name for name in ("git", "node", "npm", "ffmpeg") if not command(name)]
    if missing:
        raise SystemExit("Missing required command(s): " + ", ".join(missing) +
                         ". Install them with your operating system package manager, then rerun this installer.")
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required to run the installer.")


def install(args: argparse.Namespace) -> None:
    check_prerequisites()
    cuda = has_cuda()
    print("Voice Studio installer:", platform_summary(cuda), flush=True)
    for folder in (ROOT / "vendor", ROOT / "models", ROOT / "cache", ROOT / "logs", ROOT / "data"):
        folder.mkdir(parents=True, exist_ok=True)

    if not (ROOT / "vendor/Qwen3-TTS/pyproject.toml").is_file():
        run(["git", "clone", "https://github.com/QwenLM/Qwen3-TTS.git", "vendor/Qwen3-TTS"])
        run(["git", "-C", "vendor/Qwen3-TTS", "checkout", "--detach", QWEN_REVISION])

    if not python_in_venv().exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    py = str(python_in_venv())
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "torch==2.8.0", "torchaudio==2.8.0", *torch_install_args(cuda)])

    requirements = requirements_without_torch((ROOT / "requirements-lock.txt").read_text(encoding="utf-8"))
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix="-requirements.txt", delete=False) as handle:
        handle.write(requirements)
        requirements_path = Path(handle.name)
    try:
        run([py, "-m", "pip", "install", "-r", str(requirements_path)])
    finally:
        requirements_path.unlink(missing_ok=True)
    run([py, "-m", "pip", "check"])
    run(["npm", "--prefix", "frontend", "ci"])
    run(["npm", "--prefix", "frontend", "run", "build"])

    if not args.skip_models:
        model_args = [py, "scripts/download_models.py"]
        if args.voice_design:
            model_args.append("--voice-design")
        run(model_args)
    if args.demo:
        run([py, "scripts/create_onboarding.py"])
        if args.voice_design:
            run([py, "scripts/create_archetypes.py"])
    print("Installation complete. Run ./launch.py (or Launch-Voice-Studio.cmd on Windows).", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Voice Studio on Windows, macOS, or Linux.")
    parser.add_argument("--skip-models", action="store_true", help="Install code and dependencies without model downloads.")
    parser.add_argument("--voice-design", action="store_true", help="Also download VoiceDesign weights.")
    parser.add_argument("--demo", action="store_true", help="Generate/install packaged demo profiles and audio.")
    install(parser.parse_args())


if __name__ == "__main__":
    main()
