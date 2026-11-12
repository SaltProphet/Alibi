# Line Please

Line Please is a local voice workspace for recording, voice references,
Qwen3-TTS cloning, synthetic voice design, non-destructive audio cleanup,
multitrack arrangement, and WAV export.

The product is named **Line Please**. The `voice-studio/` directory and the
`Voice-Studio` launcher filenames are retained as implementation paths for
compatibility; they do not represent the product name.

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

Run the installer from the repository root.

### Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\voice-studio\Install-Voice-Studio.ps1 -VoiceDesign
```

### macOS or Linux

```sh
./voice-studio/install.sh --voice-design
```

The installer:

1. Creates `voice-studio/.venv`.
2. Checks out the pinned Qwen3-TTS source.
3. Selects CPU or CUDA PyTorch packages.
4. Installs the locked Python and frontend dependencies.
5. Builds the production frontend.
6. Downloads the Base and tokenizer models.
7. Downloads VoiceDesign weights when `--voice-design` is supplied.

For a source-only install without model downloads:

```sh
python voice-studio/install.py --skip-models
```

The installer does not modify global AI settings or write personal audio into
the repository outside the configured local data directories.

## Run

Start the local backend and inference worker:

```sh
python voice-studio/launch.py
```

Windows also provides:

```text
voice-studio\Launch-Voice-Studio.cmd
```

macOS/Linux provide:

```sh
./voice-studio/launch.sh
```

Open `http://127.0.0.1:8765` if the launcher does not open a browser. Stop the
services with `stop.py`, `stop.sh`, or `Stop-Voice-Studio.cmd` on Windows.

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

For implementation notes, helper setup, and historical verification records,
see the focused documents under the legacy implementation directory
`voice-studio/`.

## Development

Frontend development runs from `voice-studio/frontend`:

```sh
npm --prefix voice-studio/frontend ci
npm run dev
```

The root `npm run dev` command forwards to the frontend and accepts Vite
options, for example `npm run dev -- --host 127.0.0.1`.

Rebuild the tracked production frontend with:

```sh
npm --prefix voice-studio/frontend run build
```

Useful checks from `voice-studio/`:

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
.\Launch-Voice-Studio.ps1 -TestWorkspace -NoBrowser
.\.venv\Scripts\python.exe .\scripts\test_api.py
```

## Repository layout

| Path | Purpose |
|---|---|
| `voice-studio/frontend/` | React/Vite source and tracked production build |
| `voice-studio/backend/` | Local FastAPI audio, profile, job, session, and export API |
| `voice-studio/inference/` | Separate local Qwen inference worker |
| `voice-studio/install.py` | Cross-platform installer |
| `voice-studio/launch.py` | Cross-platform launcher |
| `voice-studio/scripts/` | Setup, model, verification, and maintenance scripts |
| `voice-studio/models/` | Downloaded local model weights; not source-controlled |
| `voice-studio/data/` | Local recordings, profiles, sessions, and exports |
| `voice-studio/logs/` | Local service and installation logs |

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
