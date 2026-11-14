# Historical: AuraVoice integration

This document describes an earlier Visual-mode implementation. Visual mode is not part of the current shipped build; retain this file only as historical reference.

This historical document describes an earlier AuraVoice reference integration.
It is not part of the current Alibi interface. The current build uses
the standard Alibi workspaces documented in the repository README.

## Workflow

1. Open Recorder & editor to record or import a clean sample. Save a voice reference using its exact transcript.
2. Open Immersive studio. Choose a saved voice in a dialogue block, enter a short line, and synthesize.
3. Play the result or download its WAV. Additional blocks generate sequentially; completed takes are saved individually, and a combined sequence creates a saved session and WAV export.
4. Choose an individual saved take before applying pitch, timbre, or vibrato. Processing creates a new copy.

Voice Reference also supports direct file import and profile saving with a name and exact transcript. There is no simulated biometric extraction. Archetype cards select visual palettes; a palette alone does not create a voice. Associated saved archetype profiles can assign voices to empty dialogue blocks.

Microphone sensing drives the visuals without recording or speaker monitoring. Use Recorder & editor to record. Fluid curves and helix are artistic animations driven by audio energy; Frequency displays analyser bins. Full, Light, and Still options control visual rendering. Zen view hides the interface; Escape restores it.

Stop halts playback and prevents additional dialogue blocks from starting. A running inference job finishes, and its completed take is preserved. Dialogue drafts persist in this browser's local storage; audio and saved sessions use the existing backend storage.

## Verification

- Production Vite build passed.
- DOM/API adapter assertions passed using explicit test responses for generation, polling, sequence sessions, mixed export, import, profile saving, processing, and draft preservation.
- The update installer ran successfully on the user's Windows installation. The user confirmed the updated interface opened and supplied an exported WAV. File inspection verified 3.04 seconds, 24 kHz, mono, 16-bit PCM, with no clipped samples.
- Listening quality, headphone playback, microphone capture through the new interface, and full regression of all editing controls remain unverified. Fixture checks do not establish real synthesis quality or complete end-to-end coverage.

## Structure

AuraStudio.jsx hosts the visual document in a same-origin iframe so its styles and canvas runtime remain separate from the editor. immersive/visual-runtime.js owns visual behavior; immersive/bridge.js connects the existing local APIs. Parent/iframe messages validate origin and source. Switching views keeps the immersive document mounted to preserve drafts and running jobs.
