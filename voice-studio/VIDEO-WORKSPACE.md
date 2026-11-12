# Video workspace

Video is a separate workspace beside Generate, Record & edit, and Arrange & export. Existing audio sessions and files retain their original formats and routes.

1. Open Video and import an MP4 or WebM (up to 250 MB and one hour).
2. Preview the video and drag across the timeline, or enter exact range start/end times.
3. Enter narration text, choose a saved voice, and click Generate & place narration.
4. Use Play range with narration to preview the placement. Native video controls preview the source picture; the range button adds the scheduled narration.
5. Export narrated MP4, inspect the rendered preview, and download it.

The original video is retained unchanged. Export encodes its picture as H.264 and the narration as AAC in an MP4. If an imported video has sound, the workspace explicitly explains that its original sound is omitted.

Speech plays at its natural speed, starting at the selected range start. A short take leaves silence. An overlong take is retained as a recording; widen the range and use Place saved take in current range, or generate shorter text. Speech is never silently cut off or accelerated. Multiple clips can be placed; overlapping clips mix with peak limiting. Remove and replace clips to change their placement.

Generation and placement reuse the existing /api/generate and /api/jobs mechanisms and local inference worker. The current Video form uses English. Projects persist separately in data/videos, and exports are in data/video-exports. Generate, remove, and export save project state; use Save video project to preserve other form/range changes before reloading. Open video project restores saved work. Generated takes remain in the standard recordings library.

FFmpeg and FFprobe are required. The Windows launcher now also discovers installed WinGet FFmpeg tools when its inherited PATH is stale. There are no new Python or JavaScript dependencies.

## Verification

- Production frontend build: PASS.
- Real Chromium import/metadata/playback of silent H.264 MP4 and VP9 WebM: PASS (12 seconds, 640 by 360).
- Pointer drag selection, exact numeric times, invalid range prevention, navigation preservation, saved project restoration: PASS.
- Real saved synthetic voice generation: PASS. Qwen generated 'Welcome to the video studio.' as a 2.00 second take; the first run took 7.19 seconds.
- Browser generate/place/export/rendered playback: PASS. A 12-second MP4 played successfully with narration starting at 2 seconds.
- Export decoded audio: PASS. RMS before narration was 0.0; during narration 0.1076; after narration 0.0.
- Real FFmpeg multi-clip placement for MP4 and WebM inputs: PASS. One-second timing tones at 2 and 6 seconds were present at their expected positions, with silence between and after them.
- Immutable source hashes, malformed inputs, partial source requests, invalid ranges, empty export rejection, overlong speech rejection: PASS.
- Browser overlong generation, take retention, wider-range placement, remove clip: PASS.
- Mobile at 390 pixels: PASS, no horizontal overflow. Browser error/warning log: zero.
- Existing audio backend import, trim, normalize, reference save, session save/reopen, WAV export: PASS.
- Existing Generate, Arrange playback/export, and Record & edit UI: checked in Chromium with real generation and WAV export.
- Existing focused-workspace lifecycle/layout regression: PASS, including visual motion on/off and cleanup.
- Existing AI helper contract checks: PASS.
- Physical microphone capture: NOT RETESTED. Record controls remain available and the recording code path was preserved.

Reproduce the isolated media/API checks using `.venv\Scripts\python.exe scripts\test_video.py` with FFmpeg/FFprobe on PATH. It creates its own fixtures and unique data/tests/video-contract-* directory. Browser verification scripts are in scripts/verify_video_*.js; they use the isolated backend on port 8875 and work/video-fixture.mp4 and .webm. They exercise the real local inference worker, so its models must be available.

## Checkpoint and scope

Before edits, current backend, frontend source/build, inference, documentation, and requirements were copied to a local backup. The launcher was copied before its edit. Existing uncommitted helper changes were preserved; no files were staged, committed, or pushed. The source and active service were verified in the working checkout. This is historical verification metadata, not a runtime path.

## Limits

Browser preview depends on supported input codecs; H.264 MP4 and VP9 WebM were tested. Export re-encodes picture to H.264 rather than making a byte-identical video stream copy. English narration only in this form; no subtitle, music, time-stretching, original-sound mixing, or video cutting controls. Export runs as a request with a ten-minute processing timeout. Large/one-hour media were not stress-tested. Save the project before reloading; an in-flight generation is not automatically reattached after a page reload. Physical microphone capture and frame-accurate audiovisual sync were not manually evaluated; exported timing was verified by decoded audio windows.

Final live check: backend restarted on port 8765 using the verified source checkout; Video workspace and /api/videos responded successfully. The local inference worker remained running. Real browser MP4 download completed, and the downloaded artifact is supplied with the verification report.
