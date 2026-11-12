param([switch]$SkipModels,[switch]$VoiceDesign,[switch]$Demo)
$ErrorActionPreference='Stop'
$python=Get-Command py -ErrorAction SilentlyContinue
if (!$python) { $python=Get-Command python -ErrorAction SilentlyContinue }
if (!$python) { throw 'Python 3.12 or newer is required. Install Python, then rerun this installer.' }
$args=@('install.py')
if ($SkipModels) { $args += '--skip-models' }
if ($VoiceDesign) { $args += '--voice-design' }
if ($Demo) { $args += '--demo' }
Push-Location $PSScriptRoot
try { & $python.Source @args } finally { Pop-Location }
