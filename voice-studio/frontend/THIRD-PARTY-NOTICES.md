# Bundled frontend dependencies

The archived supplied design reference remains at `src/immersive/reference.html` for provenance. It is not imported by the current build. The shipped frontend uses React, Vite, Inter, Lucide, and WaveSurfer.

Lucide (ISC) and Inter (SIL Open Font License) are bundled locally. Their notices are included under `public/licenses/` and copied into production output. React and WaveSurfer remain the app dependencies.

Python effects use librosa for duration-preserving pitch shifting and Pedalboard for tone shaping and modulated-delay vibrato. Effects render derivative WAVs; original recordings are preserved.
