$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$env:HF_HOME = Join-Path $root 'cache\huggingface'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
Set-Location $root
& "$root\.venv\Scripts\qwen-tts-demo.exe" "$root\models\Qwen3-TTS-12Hz-1.7B-Base" --ip 127.0.0.1 --port 7861 --dtype bfloat16 --no-flash-attn
