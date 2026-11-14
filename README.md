# Alibi

**Clone. Shape. Perform.**

Alibi is a local voice production app for dialogue and narration. Clone your voice from a recording, design a new voice from a text description, and arrange multiple voices on a timeline. Clean up takes, export a mixed WAV, or add narration to a video.

Everything runs on the host machine. The application does not require a paid
API, cloud TTS key, Docker, or an account for normal local use.

## Current interface

The shipped frontend opens in **Generate** and provides these workspaces:

- **Voices** — browse saved voices, clone a voice from a reference recording,
  or design a synthetic voice from a description.
- **Generate** — select a voice, enter text, generate speech, and manage takes.
- **Record & Edit** — record or import audio, trim it, clean it up, and save
  reusable references.
- **Transcribe** — navigation placeholder for a future dedicated transcription
  workspace.
- **Arrange** — place clips on tracks, mix them, save sessions, and export WAV.
- **Video** — create narrated video exports from local media.

Visual mode and its Three.js/Tailwind runtime are not included in the shipped
build.

## Requirements

- Python 3.12 or newer
- Git
- Node.js and npm
- FFmpeg and FFprobe on `PATH`
- Internet access for dependency and model downloads
- Several gigabytes of available disk space for models and Python packages

The installer detects `nvidia-smi`. When an NVIDIA GPU is available it installs
CUDA-enabled PyTorch; otherwise it installs CPU PyTorch. CPU inference is
supported but can be substantially slower than GPU inference.

## Install

The one-click Windows `.exe` installer is published with GitHub Releases and is not stored in the repository. The steps below also cover source setup.

Run the installer from the repository root.

### One-click Windows installer

Download `AlibiSetup.exe` from the latest GitHub Release and double-click it to
install Alibi per-user under `%LOCALAPPDATA%\Alibi`; no Python, Node.js, Git, or
FFmpeg installation is required. The installer downloads the CPU/CUDA runtime,
Base model, tokenizer, and optionally VoiceDesign weights. Allow at least 20 GB
of free space, or 24 GB when VoiceDesign is selected.

Windows SmartScreen may warn because release builds are currently unsigned.

### Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\alibi\Install-Alibi.ps1 -VoiceDesign
```

### macOS or Linux

```sh
./alibi/install.sh --voice-design
```

The installer:

1. Creates `alibi/.venv`.
2. Checks out the pinned Qwen3-TTS source.
3. Selects CPU or CUDA PyTorch packages.
4. Installs the locked Python and frontend dependencies.
5. Builds the production frontend.
6. Downloads the Base and tokenizer models.
7. Downloads VoiceDesign weights when `--voice-design` is supplied.

For a source-only install without model downloads:

```sh
python alibi/install.py --skip-models
```

The installer does not modify global AI settings or write personal audio into
the repository outside the configured local data directories.

To build the installer from source on Windows:

```powershell
.\installer\build.ps1
```

The build downloads the pinned Qwen3-TTS source, packages the application and
production frontend into a single `dist\AlibiSetup.exe`, and writes a
SHA-256 checksum beside it. Model weights are intentionally downloaded by the
installer rather than embedded in the executable. Attach both build outputs to
a GitHub Release instead of committing them.

## Run

Start the local backend and inference worker:

```sh
python alibi/launch.py
```

Windows also provides:

```text
alibi\Launch-Alibi.cmd
```

macOS/Linux provide:

```sh
./alibi/launch.sh
```

Open `http://127.0.0.1:8765` if the launcher does not open a browser. Stop the
services with `stop.py`, `stop.sh`, or `Stop-Alibi.cmd` on Windows.

The first generation loads the local model and can take a while. Later
generations reuse the loaded model. The backend and inference worker bind only
to loopback by default.

## Typical workflow

1. Open **Record & Edit** and record or import a clean reference.
2. Trim and clean the recording without changing the original file.
3. Save the reference with the exact transcript and a profile name.
4. Open **Generate**, select the profile, enter text, and generate speech.
5. Add selected takes to **Arrange**.
6. Position clips, adjust tracks, save the session, and export a mixed WAV.

For implementation notes and helper setup, see [AI-HELPERS.md](alibi/AI-HELPERS.md)
and the [documentation index](docs/README.md). Historical verification records
live under [docs/archive](docs/archive/).

## Development

Frontend development runs from `alibi/frontend`:

```sh
npm --prefix alibi/frontend ci
npm run dev
```

The root `npm run dev` command forwards to the frontend and accepts Vite
options, for example `npm run dev -- --host 127.0.0.1`.

Rebuild the tracked production frontend with:

```sh
npm --prefix alibi/frontend run build
```

Useful checks from `alibi/`:

```sh
python scripts/test_installer.py
python -m py_compile install.py launch.py stop.py
.venv/Scripts/python.exe scripts/test_dsp.py       # Windows
.venv/Scripts/python.exe scripts/test_assist.py    # Windows
```

On macOS/Linux, replace the Windows virtual-environment path with
`.venv/bin/python`.

API checks use an isolated test workspace so they do not target personal
recordings:

```powershell
.\Launch-Alibi.ps1 -TestWorkspace -NoBrowser
.\.venv\Scripts\python.exe .\scripts\test_api.py
```

## Repository layout

| Path | Purpose |
|---|---|
| `alibi/frontend/` | React/Vite source and tracked production build |
| `alibi/backend/` | Local FastAPI audio, profile, job, session, and export API |
| `alibi/inference/` | Separate local Qwen inference worker |
| `alibi/install.py` | Cross-platform installer |
| `alibi/launch.py` | Cross-platform launcher |
| `alibi/scripts/` | Setup, model, test, and maintenance scripts; see its README |
| `alibi/models/` | Downloaded local model weights; not source-controlled |
| `alibi/data/` | Local recordings, profiles, sessions, and exports |
| `alibi/logs/` | Local service and installation logs |
| `installer/` | Windows installer builder and per-user setup |
| `docs/` | Documentation index; `docs/archive/` holds historical records |
| `dist/` | Local installer build output; published through GitHub Releases, not committed |

## Privacy and safety

- Audio, profiles, sessions, and generated files remain local by default.
- Servers bind to `127.0.0.1` unless explicitly configured otherwise.
- Original recordings are preserved when edits create derivatives.
- The repository does not include personal recordings, credentials, local
  model weights, logs, or machine-specific paths.
- Review model and dependency licenses before redistribution.

## Current limitations

- CPU inference may be slow for a 1.7B voice model.
- Voice cloning quality depends on the reference recording and exact transcript.
- Transcribe is currently a placeholder navigation workspace.
- The editor is intentionally lightweight and is not a full DAW.
- There is no automatic exact-transcript verification, plugin system, time
  stretching, automation lanes, or generation cancellation.
- Video export supports the currently implemented local narration workflow,
  not full nonlinear video editing.
