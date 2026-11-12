param([switch]$SkipModelDownload)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
function Check-Exit([string]$step) { if ($LASTEXITCODE -ne 0) { throw "$step failed (exit $LASTEXITCODE)." } }
foreach ($command in @('py','git','node','npm.cmd','ffmpeg')) {
  if (!(Get-Command $command -ErrorAction SilentlyContinue)) { throw "Required command missing: $command. See the repository README." }
}
& py -3.12 --version
Check-Exit 'Python 3.12 check'
Push-Location $root
try {
  if (!(Test-Path '.venv\Scripts\python.exe')) {
    & py -3.12 -m venv .venv
    Check-Exit 'Virtual environment creation'
  }
  $python=Join-Path $root '.venv\Scripts\python.exe'
  New-Item -ItemType Directory -Force vendor,models,cache,logs,data | Out-Null
  if (!(Test-Path 'vendor\Qwen3-TTS\pyproject.toml')) {
    & git clone https://github.com/QwenLM/Qwen3-TTS.git vendor/Qwen3-TTS
    Check-Exit 'Official source download'
    & git -C vendor/Qwen3-TTS checkout --detach 022e286b98fbec7e1e916cb940cdf532cd9f488e
    Check-Exit 'Official source revision'
  }
  & $python -m pip install --upgrade pip
  Check-Exit 'pip update'
  & $python -m pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
  Check-Exit 'CUDA PyTorch installation'
  & $python -m pip install -r requirements-lock.txt --extra-index-url https://download.pytorch.org/whl/cu128
  Check-Exit 'Python dependency installation'
  & $python -m pip check
  Check-Exit 'Python dependency validation'
  & $python -c "import torch; assert torch.cuda.is_available(), 'CUDA unavailable'; print(torch.__version__, torch.cuda.get_device_name(0))"
  Check-Exit 'CUDA validation'
  if (!$SkipModelDownload) {
    & $python scripts/download_models.py
    Check-Exit 'Model download'
  }
  & npm.cmd --prefix frontend ci
  Check-Exit 'Frontend dependency installation'
  & npm.cmd --prefix frontend run build
  Check-Exit 'Frontend build'
  & $python scripts/create_onboarding.py
  Check-Exit 'Packaged audio installation'
  & $python scripts/create_archetypes.py
  Check-Exit 'Packaged character voice installation'
  Write-Host 'Setup complete. Start Launch-Voice-Studio.cmd and open http://127.0.0.1:8765'
} finally { Pop-Location }
