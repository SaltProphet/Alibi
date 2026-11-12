# Historical: immersive acoustic playground

This document describes an earlier Visual-mode implementation. Visual mode is not part of the current shipped build; retain this file only as historical reference.

Implemented October 15, 2026, on branch `codex/immersive-voice-studio`.

The new default workspace preserves the supplied HTML at `frontend/src/immersive/reference.html`. A React component hosts its adapted document in a same-origin frame, keeping its CSS and DOM isolated from the established recording editor and timeline. The original file in Downloads is untouched. The supplied layout, voice cards, color transitions, particle/helix/vortex/dust fields, Zen mode, waveform modes, carrier-tone instrument, and script presets remain available.

## Connected features

- Nova Prime, Atlas Deep, Cyra Synth, and Echo ASMR each select an actual synthetic reference profile. Packaged previews and exact transcripts are stored under `content/archetypes/`. The Nova reference uses the existing friendly synthetic host; the other three were generated with the local VoiceDesign model. Voice profiles are installed independently in personal and demo storage.
- Synthesize & Play submits a real asynchronous Qwen Base generation job, reports errors, and plays the completed WAV. The playback button pauses/resumes actual audio; the progress bar seeks it.
- Microphone sensing and generated audio feed Web Audio analysers. Visual intensity reacts to audio; frequency bars use measured frequency bins. Artistic helix and fluid modes preserve the supplied style.
- Base pitch, timbre color, and vibrato render to a new WAV through Apply & preview FX. Pitch uses librosa, tone uses Pedalboard shelf filters, and vibrato uses wet modulated delay. Settings are stored in derivative metadata. Original audio is untouched. Reset restores neutral speech settings.
- The frame's Download WAV link points to the current processed audio, and Open in editor hands that asset to the existing editor. Recording, cleanup, multitrack mixing, WAV export, session persistence, and spoken welcome remain available through workspace tabs.
- Full, Light, and Still visual modes are available. Reduced-motion settings start Still mode. Leaving the playground pauses its playback, stops microphone sensing, and suspends animation.
- All fonts, Three.js, icons, and compiled utility CSS are served locally. Notices are bundled under `/licenses/`.

## Verification

Used a separate backend on loopback port 8875 with storage under `data/tests/immersive`, not personal recordings.

- Four profiles seeded from packaged synthetic references.
- Actual Atlas speech generated through the new UI: 5.36 seconds, 24 kHz WAV; peak PyTorch allocation approximately 4.36 GiB.
- Actual pitch/color/vibrato derivative rendered and played. A controlled signal test shifted 440 Hz to 880 Hz at +12 semitones, preserved duration, and verified vibrato changes audio.
- Browser path completed: choose voice -> enter dialogue -> generate/play -> render effects -> open editor -> add clip -> save session -> export mixed WAV. Export verified as 48 kHz stereo, 5.36 seconds.
- Tested actual microphone permission/sensing, seeking, Zen entry and Escape restore, visualization mode and quality switching, editor handoff, and mobile layout at 430px with no horizontal document overflow.
- Fixed an inherited invisible Zen restore button intercepting clicks and an absent optional meter element during initial integration. Final tested browser console had no errors.
- Existing filter/fade/mute/gain/mix signal tests passed; Python dependency checks passed; frontend production build passed.
- Production dependencies report zero vulnerabilities with `npm audit --omit=dev`. Build tooling currently reports upstream development-only watcher dependencies; these are not served to the browser. No force upgrade was applied to unrelated packages.
- Restarted only this app's backend/demo processes to load effects support. The inference worker, personal audio, existing sessions, and protected tunnel were retained. Both application instances report four voices and the new effects schema. Anonymous shared-link requests still redirect to authentication.

Evidence remains locally under `data/tests/immersive-verification.json` and the immersive screenshots. Effects are rendered previews rather than continuous real-time pitch processing. The spectral view is a live frequency-bar visualization. Character styles are synthetic voice designs, not identities of real people.
