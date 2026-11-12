# Historical: unified workspace — October 15, 2026

This document describes an earlier frontend checkpoint. It is not a specification of the current shipped build; Visual mode is no longer included.

Checkpoint: Git tag `checkpoint/before-unified-studio-20261015` at commit `11a3e63`. The supplied HTML in Downloads and its preserved source copy are untouched. To inspect the old application without overwriting current work, create a separate checkout from that tag.

The active frontend now uses shared React state rather than the iframe workspace boundary. `StudioStage.jsx` provides native generation controls, character/profile selection, reference loading, a selected-take audio player, and a Web Audio analyser visualizer. `main.jsx` retains recording, imports, WaveSurfer trimming, non-destructive cleanup/effects, profile saving, timeline geometry, mixing, export, and session persistence. `immersive-shell.css` arranges these in one responsive page. The spoken-welcome panel and workspace tab bar are removed; files remain intact.

No inference/API changes, package installations, cloud API calls, or changes to unrelated services were needed. The existing backend serves the rebuilt frontend immediately; refresh the browser. The personal and demo workspaces both use this frontend while retaining separate data.

## Functional verification

All generated test data is under `data/tests/immersive`, through loopback test port 8875.

- Real Atlas Deep reference loaded; Qwen generated `d31328fef42d487c95b753e73027a779.wav`, 5.440 seconds at 24 kHz, nonempty finite audio. Inference took 21.50 seconds; peak allocated GPU memory was 4.36 GiB.
- Browser audio playback advanced to 0.699 seconds, readyState 4, paused false.
- Browser import of the packaged Nova reference preserved original bytes (SHA256 equality); a new reusable profile was saved.
- Browser microphone capture through a local audio device produced a 1.26-second recording. This proves capture/import, not the acoustic quality of a future external microphone.
- Waveform editor trimming 0.2–4.5 seconds, normalization, high-pass, and fade-in produced a separate 4.30-second edited WAV.
- Added edited clip to timeline; saved Unified workspace TEST; exported a 4.30-second, 48 kHz stereo PCM WAV.
- Page reload and saved-session reopening restored the clip; mix playback and stop worked. Stopping and restarting the isolated backend also preserved the session and restored its clip.
- Zen entry, Escape restoration, mobile 430 px width with no document overflow, and browser console with zero errors passed.

Limitations: voice direction from the hosted design is not silently mapped to Base cloning; it would need a separate VoiceDesign workflow. The new visualizer is a lightweight Canvas/Web Audio view, not the older Three.js particle scene. The older scene and carrier instrument remain in the checkpoint/source but are not exposed in this consolidated UI. Existing sessions persist audio arrangement, not unsaved dialogue or temporary form settings.
