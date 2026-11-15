# Scripts

Run scripts from the `alibi/` directory with its virtual environment: `.venv/Scripts/python.exe scripts/<name>.py` on Windows or `.venv/bin/python scripts/<name>.py` on macOS/Linux. Browser scripts are Playwright code blocks run through `playwright-cli run-code --filename`.

## Runtime and setup

| Script | Purpose |
|---|---|
| `run_server.py` | Starts the backend (`backend`, port 8765), inference worker (`inference`, port 8766), or demo (`demo`, port 8767). Used by the launchers. |
| `run_test_server.py` | Starts an isolated test instance on port 8875. Never opens personal data. |
| `download_models.py` | Downloads the Base and tokenizer Qwen models; add `--voice-design` for VoiceDesign weights. |
| `share_demo.py` | Starts or stops the email-protected Cloudflare demo. Never creates an open tunnel. |
| `create_onboarding.py` | Regenerates packaged walkthrough audio and profiles. |
| `create_archetypes.py` | Regenerates the four bundled sample character voices. |
| `create_narrator.py` | Regenerates the bundled narrator reference. |

## Automated tests

These use isolated workspaces or temporary directories. `test_api.py` requires `Launch-Alibi.ps1 -TestWorkspace -NoBrowser`; `test_demo_functional.py` requires the demo service on port 8767.

| Script | Covers |
|---|---|
| `test_api.py` | Import, edit, profile, generation, session, and export API contracts. |
| `test_dsp.py` | Filters, fades, mute, and mix gain at the signal level. |
| `test_assist.py` | Writing/transcription helper contracts with stubbed services. |
| `test_video.py` | Video media contracts using real FFmpeg. |
| `test_installer.py` | Installer platform and runtime-selection helpers. |
| `test_buildinfo.py` | Version and build-stamp resolution for checkouts and installed copies. |
| `test_onboarding.py` | Packaged walkthrough and sample-profile integrity. |
| `test_demo_functional.py` | Demo workspace isolation from personal data. |
| `test_sharing.py` | Live sharing checks; run from the repository root while the demo tunnel is active. |
| `test_immersive_audio.py` | Legacy DSP and archetype check; expects a test server on port 8875. |
| `phase1_test.py` | One-off CUDA model smoke test. Requires a local GPU and downloaded models. |

## Browser verification

These are Playwright scripts, not Python. They expect a running app (port 8765 or the isolated test server on 8875) with seeded test data.

| Script | Covers |
|---|---|
| `verify_focused_browser.js` | Current navigation and responsive layout. |
| `verify_recording_management.js` | Recording panel search, folders, and selection. |
| `verify_video_import.js` | Video import and navigation. |
| `verify_video_generation.js` | Narrated video generation. |
| `verify_video_edges.js` | Range playback and edge cases. |
| `verify_video_audio_regression.js` | Audio workspace still works after video changes. |
| `verify_video_live.js` | Full live video export. |
