# Local AI helpers

The normal Generate / Record & edit / Arrange & export workflow remains intact.

* **Script assistant** drafts or rewrites the script. **Rewrite** beside a dialogue block receives surrounding block text as context and changes only that block after review. **Shape description** edits a voice description. All suggestions open in an editable dialog and require **Use draft**; discard keeps the original text.
* In **Record & edit → Save as a voice reference**, **Transcribe selected recording** transcribes the entire saved audio asset (up to ten minutes). Apply trims first to transcribe a derivative. Review the result, then use it as a reference transcript or script. Recognition is not a guarantee of exact words. Original audio remains unchanged.
* **Design a voice**, collapsed under generation, uses natural-language pitch, timbre, pace and delivery descriptions with Qwen VoiceDesign. Generate a short sample, listen, review the prefilled words, and save it through the existing reference form. The resulting profile is marked synthetic and works in the existing dialogue sequence. A description does not alter an existing cloned voice.

## Models and installation

Writing uses the existing loopback Ollama service (`127.0.0.1:11434`) and defaults to `gpt-oss:20b`. Set `VOICE_STUDIO_AI_MODEL` before launching to select another already installed model. Missing service/model failures appear in the dialog; the studio never pulls Ollama models. The request uses `keep_alive: 0` to release the writing model after its reply. Drafting may take a minute or more on this machine.

Transcription uses faster-whisper 1.2.1 with **CPU int8**, four threads, automatic language detection and VAD. This avoids an additional GPU model. Install into the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-assist.txt
.\.venv\Scripts\hf.exe download Systran/faster-whisper-small --local-dir models/faster-whisper-small --include model.bin config.json tokenizer.json vocabulary.txt
```

The small multilingual model needs roughly 0.5 GB of disk. `VOICE_STUDIO_ASR_MODEL` can point to another local CTranslate2 Whisper model directory. Model loading uses `local_files_only=True`; no model is downloaded by a transcription request. Nemotron/NeMo is not installed or integrated.

Voice design uses the optional `models/Qwen3-TTS-12Hz-1.7B-VoiceDesign` model and the existing Qwen tokenizer. Fresh installs download Base and tokenizer weights by default; add `--voice-design` to `install.py` to download VoiceDesign weights. The worker holds one Qwen model at a time, unloading before switching Base ↔ VoiceDesign. Allow initial model loading time after a switch. Cloning continues to use Base and the exact reference transcript.

## Storage and execution

Transcription creates `data/transcripts/<id>.json` with a new ID, source asset ID, text, timestamp, model name, language and segment times. This metadata survives restart. Reviewed corrections live in the reference/profile when saved; the raw transcription remains provenance. Voice samples are ordinary immutable audio assets with the description and requested words in their metadata. Existing audio, profile and arrangement IDs and formats remain valid.

Writing suggestions, helper jobs and unsaved form values do not survive page reload/server restart. Helper requests share the existing one-job queue; conflicting jobs are rejected visibly. Speech recording and helpers are mutually exclusive in the UI. Do not close the assistant while a request is in flight; review or discard after it completes. There is no inference cancellation.

All helpers are disabled in the shared demo, both in the UI and on the API. No public AI endpoint or tunnel is created. Personal audio/text stays on the PC; local model installation requires a one-time network download. Existing demo generation and workspace separation remain intact.

For isolated verification only, `VOICE_STUDIO_WORKER_URL`, `VOICE_STUDIO_MODELS`, `VOICE_STUDIO_DATA`, and `HF_HOME` can override worker location, model storage and data/cache directories. Normal launch requires none of these. These are operator environment settings, never browser-supplied paths or URLs.

## Verification

`python scripts/test_assist.py` checks transcript provenance, original audio integrity, invalid inputs, absent-model errors, cross-origin rejection and demo isolation using isolated data and stubbed inference. Real inference and browser verification are reported separately in the delivered integration report.

Sources: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [Ollama chat API](https://docs.ollama.com/api/chat), [Qwen VoiceDesign and cloning](https://github.com/QwenLM/Qwen3-TTS).
