# Historical: Alibi visual review

Verified October 15, 2026 (America/New_York). Branch: `design/obsidian-acoustic-shell`.

## Evidence and starting state

The Git repository root is the parent project directory. The application lives in `voice-studio/`.
The checkout was clean on `main` at `c0dcc54a4b2da57b498257e857a6b605c5599005`.
The linked repository remote returned the same default HEAD during the historical inspection. This verifies the remote default HEAD at inspection time; it is not a review of every remote branch or issue.

The supplied `ai_voice_studio3.html` was recovered from the referenced conversation and read directly. Its visual vocabulary includes monochrome glass, silver type, atmospheric fog, concentric/helix forms, and slow motion. Its runtime also uses CDN libraries, microphone analysis, a WebGL canvas, and a Space-key HUD toggle. Those runtime behaviors were not imported.

## Directions considered

These are proposed design interpretations, not claims of novel inventions or a competitive product survey.

1. **Obsidian / Acoustic — selected by the user.** Near-black layered panels, silver typography, restrained mint audio cues, atmospheric drifting light, fine diagonal field lines, and acoustic rings around the welcome panel.
2. **Signal / Instrument.** Graphite console surfaces, amber indicators, sharper geometry, dense measurement grids, tactile transport controls.
3. **Ivory / Editorial.** Warm pale surfaces, ink text, copper accents, editorial spacing, subtle paper-like depth.

## Functionality and styling boundary

| Area | Critical behavior | Treatment |
| --- | --- | --- |
| `frontend/src/main.jsx` | React state, API requests, recording permissions/MediaRecorder, WaveSurfer regions, generation polling, Web Audio mixing, session operations | One added stylesheet import; all remaining source unchanged |
| `frontend/src/AudioWelcome.jsx` | Audio player reference, pause on collapse, open-in-editor callback | Unchanged |
| `.wave` and its shadow DOM | WaveSurfer owns decoding, playback, region handles | Style outer container only |
| `.lane`, `.clip`, `.track-head` | Pointer hit testing, `data-track`, absolute clip positions | Preserve class hooks, 55 pixels/second, 110px grid, 180px track header, clip height and offsets |
| `backend/` | Imports, original preservation, DSP, profiles, jobs, sessions, WAV exports, local-origin protections | Unchanged |
| `inference/` | Model loading and speech inference | Unchanged |
| Existing CSS | Base layout and original fallback appearance | Retained; new theme overrides it |

## Incremental implementation

1. Establish clean local/remote baseline, inspect reference, map audio and DOM boundaries, run DSP baseline, create a separate branch.
2. Add `studio-theme.css` after the existing stylesheet. Define reusable color, surface, spacing, radius, and motion tokens; restyle existing components without replacing markup or handlers.
3. Add non-interactive CSS atmosphere and acoustic rings. Add visible keyboard focus, reduced-motion handling, forced-color fallbacks, and responsive layout rules.
4. Exercise existing APIs and browser workflows using isolated test storage. Fix narrow-screen file-input overflow discovered during browser checks.
5. Rebuild the tracked production assets and prepare this review record. No merge or remote publication.

The CSS uses local system fonts and adds no runtime libraries, external font requests, audio listeners, keyboard shortcuts, or microphone access. Atmosphere is decorative, not reactive to audio. No WebGL helix was implemented; adding that would require a separately measured rendering layer and performance review.

## Changed files

- `frontend/src/studio-theme.css` — new reusable theme and responsive/accessibility rules.
- `frontend/src/main.jsx` — import the new theme.
- `frontend/dist/index.html` — updated production asset references.
- `frontend/dist/assets/index-_aRLtCxC.css` — rebuilt combined styles, replacing `index-0wQ9h5bL.css`.
- `frontend/dist/assets/index-BiRvLE8k.js` — rebuilt bundle, replacing `index-ChOzmwMT.js`.
- `VISUAL-OVERHAUL.md` — this audit, implementation, and verification record.

## Verification

**Passed:**

- Production Vite build after final CSS correction; 27 modules transformed.
- Existing `scripts/test_dsp.py`: high-pass attenuation, fade endpoints, clip offsets and trims, track gain/mute, clipping prevention.
- Existing `scripts/test_api.py`, copied to a scratch harness with only the root, isolated endpoint/data directory, and evidence filenames adjusted: WAV/MP3/FLAC import; original bytes preserved; cleanup/trim/fades/normalization; profile creation; session save/reopen; non-silent 48kHz stereo WAV export; invalid input and foreign origin/host rejection.
- Real Chromium browser: WaveSurfer media playback clock advances; stop; exact trim fields; add clip; Web Audio mix start/stop; pointer drag between tracks; approximately 2 seconds at the expected 55px/second mapping; precise position editing; mute/unmute; mixed WAV export; new session; save/reopen restores clip position; cleanup creates derivative.
- No document-level horizontal overflow at 1280, 1024, 700, and 390px, including a populated arrangement. Timeline scrolling remains local to its container.
- Reduced-motion preference disables atmospheric animation. No browser page errors during the successful workflow run.
- Spoken welcome loads into the waveform, collapses/restores, and fits at desktop and mobile widths. Screenshots visually inspected.
- `git diff --check` passes. Main source diff contains only the theme import.

Test servers: isolated backend `127.0.0.1:8775`, frontend preview `127.0.0.1:5178`. Test API/browser writes use `data/tests/visual-overhaul/`. Existing studio/demo/inference services were not restarted. A copy of the existing synthetic walkthrough was imported into test storage to check onboarding; personal metadata and recordings were not edited.

## Risks and limits for review

- Hardware microphone capture and permissions were not exercised. The recording code is unchanged.
- No fresh speech-generation job was submitted. Profile persistence passed; generation quality, latency, and job completion are unverified in this run.
- Browser media clock advancement and DSP/export checks do not establish audible quality through the user's speakers or headphones.
- Chromium was exercised; Firefox, Safari, physical touch dragging, and assistive-technology navigation were not tested. Focus and forced-colors rules were added, but a complete accessibility audit was not performed.
- No GPU/CPU performance benchmark or audio-underrun measurement. The decorative layer has a single slow CSS animation and can be disabled through the OS reduced-motion preference.
- The API script is an adapted existing test, not the unchanged launcher-driven test, because the personal studio was already running. Existing services were left alone.
- Production `dist/` is tracked and was rebuilt in this checkout. A browser refresh of a backend serving this checkout can show the new appearance before any merge. Branch separation protects Git history, not the running checkout's files.
- The layer overrides legacy CSS. Future base stylesheet changes should be checked against this theme, especially responsive rules and native form controls.

Review before merging. To revert the visual layer in a future change, remove its import and rebuild; the original stylesheet and application logic remain available.
