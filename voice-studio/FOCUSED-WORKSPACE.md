# Focused workspace — October 17, 2026

## Checkpoint and delivery

Starting commit: `7fe85fc806a0264560123a7ea656fb016de18ae3`.
Checkpoint tag: `checkpoint/before-focused-workspace-20261017`.

The Line Please frontend was rebuilt and deployed to the separate running installation's frontend/dist. Its previous frontend is backed up under logs/deployments/focused-20261017-013108/dist in this repository checkout. Only static frontend files were deployed; no backend, model, private data, service, or sharing configuration was changed. Both source and deployment manifests were checked. Open http://127.0.0.1:8765/ and refresh; use the existing installation's launcher when stopped.

Source work is saved on codex/immersive-voice-studio, without merging main. The unrelated output/ directory, local tests, model weights, logs, and personal data are not part of this change.

## Implementation

- Generate speech is the default. Persistent Record & edit and Arrange & export navigation exposes the clip count. Searchable Recordings uses a modal drawer with Escape, close-on-selection, and focus return to its actual opener.
- All audio operations, generation polling, sequence drafts, and form state are owned by React. Existing auravoice-dialogue drafts remain readable and use the same local-storage key. Multiple generated blocks still save their individual takes, a combined arrangement, and a mixed WAV.
- The selected recording player provides Play/Pause, Edit, Add to arrangement, destination track, and Download WAV. Comparison and waveform playback stop other playback. Recording and generation are mutually exclusive; a global Stop recording remains available during navigation.
- Trims persist per asset across view changes. WaveSurfer is created only when the editor is visible and destroyed on exit. Original inputs remain immutable; processing creates derivatives.
- New arrangement clips append at the latest end on the destination track. Empty tracks start at zero. New clips are highlighted; drag and numeric fields still allow intentional overlap.
- Visual mode is presentation only: Helix, Fluid, Dust, playback, and Zen. It mounts only when opened, defaults to Motion Off, and has an explicit one-shot/continuous scheduler. Layout cleanup disposes audio/WebGL resources, observers, and the animation loop before the iframe is removed. Standard views do not render the former StudioStage canvas or animated background.
- Backend routes, inference worker, profile identifiers, session schema, and audio DSP were unchanged. Legacy adapter/template sources remain in the repository for reference but are no longer imported by the active visual component.

## Verified functional results

All generated data used the separate data/tests/focused-20261017 folder accepted by the running inference worker. Local downloaded WAVs and screenshots are under data/tests/focused-refactor in the repository checkout.

| Check | Result |
|---|---|
| Production build | PASS |
| Real single-voice generation and navigation during inference | PASS: 3.12 s output, 12.70 s inference, 4.29 GiB peak allocated GPU memory |
| Browser playback | PASS: decodable audio; playback time advanced while paused=false |
| Import and original preservation | PASS: packaged Nova WAV imported; original SHA256 unchanged |
| Reference form and saved profile | PASS: values and expanded panel survived navigation; profile saved |
| Trim, normalization, high-pass, fade | PASS: 2.40 s derivative; peak -1.00015 dBFS; no sample clipping |
| Before/After exclusivity | PASS: starting After paused Before |
| Append and track selection | PASS: positions 0 and 2.4 on Voice 1, then 0 on empty Voice 2 |
| Intentional overlap and dragging | PASS: numeric overlap restored; real pointer drag moved a clip between tracks to 2.91 s |
| Mixed export and download to disk | PASS: 4.80 s, 48 kHz stereo WAV, peak 0.98999 |
| Volume/mute and arrangement playback | PASS: 0.50 volume and mute restored; play/stop worked |
| Reload and test-server restart | PASS: three clips restored at 0, 1, 0 with volume 0.50 and mute |
| Dialogue drafts and two voices | PASS: legacy-format drafts survived reload; two real takes and 3.12 s combined WAV saved |
| Stop sequence | PASS: one request completed; later block not submitted; take retained |
| Later-block failure | PASS with explicit test-only HTTP 500 injection: first real take remained saved, second-block error shown |
| Microphone capture/navigation | PASS: actual device capture imported; generation disabled during capture; global Stop worked across views |
| Denied microphone permission | PASS: clear Permission denied error |
| Cancel/late permission and dismissal | PASS using explicitly synthetic permission timing/error injection; real late stream ended after cancellation |
| Drawer keyboard/focus | PASS: search, Escape, return to Choose recording; selection closes drawer |
| Primary control visibility | PASS at 1041 x 511: Generate bottom y=353, Record y=256.1, Export y=209 |
| Mobile width/scroll | PASS at 430 x 900: no horizontal document overflow and no nested vertical scrolling surfaces in active standard views |
| Live deployment | PASS: Generate default, zero iframe, profile groups loaded; fresh browser console had zero errors |

## Rendering measurements

Chrome DevTools Protocol Performance counters and devtools.timeline traces, same automated browser and viewport, 1.2-second idle samples after settling. No audio was playing during these samples.

| Mode | Main-thread task time | Script time | Animation callbacks | Paint events |
|---|---:|---:|---:|---:|
| Standard Generate | 8.84 ms | 0 ms | 0 | 0 |
| Visual, Motion Off | 0.56 ms | 0 ms | 0 | 0 |
| Visual, Motion On | 58.36 ms | 25.32 ms | 73 | 22 |

Motion Off's frame counter remained unchanged. After leaving Visual mode, instrumentation confirmed disposed=true, pending=false, and zero iframes. A synthetic hidden-document event cancelled pending animation; foreground resumption obeyed the motion setting.

These short samples confirm lifecycle behavior, not a general CPU/GPU speedup or a diagnosis of the earlier choppiness. The headless browser kept document.hidden=false when another tab was opened, so actual OS/browser foreground/background transitions still need a manual check. GPU utilization was not isolated or benchmarked.

Reproduce layout/lifecycle checks against port 8875 with:

    npx --yes --package @playwright/cli playwright-cli -s=focused open http://127.0.0.1:8875/
    npx --yes --package @playwright/cli playwright-cli -s=focused run-code --filename=voice-studio/scripts/verify_focused_browser.js

Run from the repository root. The script refuses another port and labels synthetic visibility injection explicitly.

## Limits and encountered errors

- The initially selected test data folder was outside the separate live worker's allowed root; generation was rejected with Audio must be inside the studio data folder. Testing moved to its dedicated test subfolder without changing the worker's path guard or private library.
- Real capture was verified, but subjective microphone sound quality and physical permission-prompt dismissal were not. Dismissal/cancellation error paths used explicit test injection; no product feature is mocked.
- Some test locators initially targeted collapsed panels or exact wrapping-label text. Tests were corrected to expand panels and use their verified accessible roles. Expanded reference state was also preserved in the application.
- A build launched with npm --prefix from the repository root hit sandbox spawn EPERM. Running the normal build in frontend/ succeeded.
- No new inference engine, transcription integration, simultaneous recording/generation, schema migration, or new dependency was added. Stop sequence is not active-job cancellation. Unsaved form state is not included in arrangement files.
