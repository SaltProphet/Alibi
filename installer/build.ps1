param(
  [switch]$SkipQwenDownload,
  [switch]$SkipPyInstallerInstall
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$build = Join-Path $root 'build\installer'
$payload = Join-Path $build 'payload'
$output = Join-Path $root 'dist'
$revision = '022e286b98fbec7e1e916cb940cdf532cd9f488e'
$qwenArchive = Join-Path $build 'qwen.zip'

if (!$SkipPyInstallerInstall) {
  python -m pip install --user pyinstaller
}

Remove-Item $build -Recurse -Force -ErrorAction SilentlyContinue
New-Item $payload -ItemType Directory -Force | Out-Null
New-Item $output -ItemType Directory -Force | Out-Null

$source = Join-Path $payload 'voice-studio'
Copy-Item (Join-Path $root 'voice-studio') $source -Recurse -Force
foreach ($relative in @('.venv', 'cache', 'data', 'logs', 'models', 'node_modules', 'frontend\node_modules', 'vendor')) {
  Remove-Item (Join-Path $source $relative) -Recurse -Force -ErrorAction SilentlyContinue
}

$vendor = Join-Path $source 'vendor\Qwen3-TTS'
if (!(Test-Path (Join-Path $vendor 'pyproject.toml'))) {
  if ($SkipQwenDownload) { throw 'Qwen3-TTS source is missing and -SkipQwenDownload was supplied.' }
  New-Item (Split-Path $qwenArchive) -ItemType Directory -Force | Out-Null
  $url = "https://github.com/QwenLM/Qwen3-TTS/archive/$revision.zip"
  Write-Host "Downloading pinned Qwen3-TTS source..."
  Invoke-WebRequest -Uri $url -OutFile $qwenArchive
  $extract = Join-Path $build 'qwen'
  Expand-Archive $qwenArchive -DestinationPath $extract -Force
  $qwenRoot = Get-ChildItem $extract -Directory | Select-Object -First 1
  New-Item (Split-Path $vendor) -ItemType Directory -Force | Out-Null
  Copy-Item $qwenRoot.FullName $vendor -Recurse -Force
}

$installerPayload = Join-Path $payload 'installer'
New-Item $installerPayload -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'uninstall.py') $installerPayload -Force
if (!(Test-Path (Join-Path $source 'frontend\dist\index.html'))) {
  throw 'Production frontend is missing. Run npm --prefix voice-studio/frontend run build first.'
}

Push-Location $root
try {
  python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name AlibiSetup `
    --add-data "$payload;payload" `
    installer\setup.py
} finally {
  Pop-Location
}

$exe = Join-Path $output 'AlibiSetup.exe'
if (!(Test-Path $exe)) { throw "PyInstaller did not create $exe" }
$hash = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content (Join-Path $output 'AlibiSetup.exe.sha256') "$hash  AlibiSetup.exe"
Write-Host "Created $exe"
Write-Host "SHA256: $hash"
