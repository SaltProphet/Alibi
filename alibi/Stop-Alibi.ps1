$ErrorActionPreference='Stop'
$sharing=Join-Path $PSScriptRoot 'scripts\share_demo.py'
if (Test-Path $sharing) {
  & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') $sharing stop
}
$script=Join-Path $PSScriptRoot 'scripts\run_server.py'
$matches=Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -and $_.CommandLine.Contains($script) }
foreach ($process in $matches) { Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host 'Stopped this Alibi backend and inference worker.'
