# Alibi Build Plan

## Current state

- [x] UI redesign steps 1–5 exist on `ui/05-voices`.
- [x] Visual mode was removed from the active React UI and frontend source.
- [x] Visual-only runtime files, Three.js, Tailwind, and unused font packages were removed from the frontend build.
- [x] Production `dist/` was rebuilt successfully.
- [x] The live Vite UI was checked: the Visual navigation button is absent.
- [x] Generated asset references resolve, the production bundle contains no Visual/Three.js references, and removed packages are absent from `package-lock.json`.
- [ ] The changes are committed.
- [ ] `ui/05-voices` is fast-forwarded into `main`.
- [ ] Documentation and browser-verification scripts reflect the shipped UI.
- [ ] Cross-platform installer and CPU/CUDA runtime selection are documented and verified.
- [ ] Tracked build-facing files contain no personal paths, usernames, device labels, or repository-owner identifiers.
- [ ] Final backend, API, DSP, and frontend checks are run.
- [ ] `main` is pushed to `origin`.

## Scope and constraints

- Ship the current native React workspace without a Visual mode.
- Keep `frontend/src/immersive/reference.html` only as an archived supplied reference; it is not part of the build.
- Keep `dist/` tracked and rebuild it from the current source.
- Do not modify `models/`, `data/`, `logs/`, or `.venv/`.
- Do not stage or delete the unrelated untracked files under `demos/`.
- Use `git merge --ff-only ui/05-voices` when updating `main`.
- Push only to the configured `origin` remote.

## Remaining work

### 1. Documentation and verification truth pass

- [ ] Update the root `README.md` to describe the current default Generate workspace and current navigation, removing claims about Immersive studio, AuraVoice visuals, and Classic view.
- [x] Replace the stale nested `voice-studio/README.md` with the repository-root README and remove the duplicate guide.
- [ ] Update `voice-studio/AI-HELPERS.md` so VoiceDesign weight requirements and installation/opt-in behavior are explicit for fresh installations.
- [ ] Mark `voice-studio/AURAVOICE.md`, `voice-studio/UNIFIED-STUDIO.md`, and `voice-studio/IMMERSIVE-STUDIO.md` as historical documents, rather than describing Visual mode as shipped behavior.
- [ ] Update `voice-studio/frontend/THIRD-PARTY-NOTICES.md` so it no longer claims that deleted `AuraStudio.jsx` or `immersive/bridge.js` are active build components.
- [ ] Update or retire `voice-studio/scripts/verify_focused_browser.js`; remove assertions that require a Visual button, iframe, Zen mode, or visual cleanup lifecycle, and retain checks for the current screens and responsive layout.
- [x] Add `voice-studio/install.py` with CPU/CUDA detection, portable dependency setup, optional model downloads, and platform-neutral launch/stop scripts.
- [x] Add `voice-studio/install.sh`, `launch.sh`, `stop.sh`, and the Windows installer wrapper.
- [x] Remove tracked personal paths and device identifiers from build-facing documentation and browser-verification scripts.
- [ ] Decide whether older audit/checkpoint documents such as `FOCUSED-WORKSPACE.md`, `VISUAL-OVERHAUL.md`, and `VIDEO-WORKSPACE.md` need historical banners. Do not rewrite their historical evidence; only prevent them from being mistaken for current implementation documentation.

### 2. Commit the frontend removal

- [ ] Review the staged file list and ensure it contains only the Visual removal, dependency/lockfile changes, license cleanup, frontend source changes, and rebuilt `frontend/dist/`.
- [ ] Leave unrelated `demos/` files unstaged.
- [ ] Run `npm.cmd --prefix voice-studio/frontend run build` one final time after the docs/script pass if any frontend files change.
- [ ] Commit the frontend work with a focused message such as `Remove Visual mode from shipped frontend`.

### 3. Fast-forward `main`

- [ ] Confirm `main` is still an ancestor of `ui/05-voices`.
- [ ] Switch to `main`.
- [ ] Run `git merge --ff-only ui/05-voices`.
- [ ] Confirm the resulting history contains the five UI commits plus the Visual-removal/build commit.

### 4. Final verification

- [ ] Start an isolated workspace without opening a browser:

  ```powershell
  .\voice-studio\Launch-Voice-Studio.ps1 -TestWorkspace -NoBrowser
  ```

- [ ] Confirm `http://127.0.0.1:8765/api/health` reports the backend ready.
- [ ] Run API and audio checks from `voice-studio/`:

  ```powershell
  .\.venv\Scripts\python.exe .\scripts\test_api.py
  .\.venv\Scripts\python.exe .\scripts\test_dsp.py
  .\.venv\Scripts\python.exe .\scripts\test_assist.py
  ```

- [ ] Open the built app served by port 8765 and verify that Generate, Voices, Record & Edit, Arrange, Transcribe, and Video load without console errors.
- [ ] Confirm Visual is absent from the navigation and there is no Visual iframe/canvas loaded in the standard workspace.
- [ ] Confirm no frontend asset requests return 404.
- [ ] Stop the test workspace and confirm the final working tree contains only intentionally retained changes plus the unrelated pre-existing untracked demo files.

### 5. Publish

- [ ] Review `git diff main..HEAD` and `git status` on `main`.
- [ ] Push with:

  ```powershell
  git push origin main
  ```

- [ ] Confirm local `main` and `origin/main` point to the same commit.

## Deferred follow-up work

These items are not required to ship the Visual removal and should not be mixed into the release commit unless explicitly requested:

- Restyle the Video workspace to the new design system.
- Implement the Transcribe screen instead of its placeholder.
- Split the large `frontend/src/main.jsx` into smaller components.
- Remove or archive unrelated dead components such as `AudioWelcome.jsx`.
- Add profile/folder deletion improvements and prune obsolete job data.
- Add CI and automated browser coverage for the current navigation.
- Resolve any remaining model-download/setup gaps beyond documenting VoiceDesign weights.
- Decide whether archived design references and historical audit files should eventually move out of the active frontend tree.
