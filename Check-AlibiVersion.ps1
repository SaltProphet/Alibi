<#
.SYNOPSIS
  Reports whether the repository, GitHub, the build stamp, and the running app agree.

.DESCRIPTION
  Prints one verdict per layer so a stale build or a stale install is obvious.
  Exit codes: 0 = everything matches, 1 = something is stale, 2 = cannot tell
  because the app is not running or origin/main has not been fetched.

.EXAMPLE
  .\Check-AlibiVersion.ps1

.EXAMPLE
  .\Check-AlibiVersion.ps1 -Offline
#>
[CmdletBinding()]
param(
  [switch]$Offline,
  [string]$Url = 'http://127.0.0.1:8765'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
  throw 'git is not installed or not on PATH.'
}

function Invoke-Git {
  param([string[]]$Arguments)
  $output = & git -C $root @Arguments 2>$null
  if ($LASTEXITCODE -ne 0) { return $null }
  return (@($output) -join "`n").Trim()
}

function Format-Sha {
  param([string]$Sha)
  if ([string]::IsNullOrWhiteSpace($Sha) -or $Sha.Length -lt 7) { return $Sha }
  return $Sha.Substring(0, 7)
}

function Write-Row {
  param([string]$Name, [string]$Detail, [string]$Verdict, [string]$Color)
  Write-Host ('  {0,-12} {1,-32} {2}' -f $Name, $Detail, $Verdict) -ForegroundColor $Color
}

if (!$Offline) {
  & git -C $root fetch origin --prune --quiet 2>$null
}

$head = Invoke-Git @('rev-parse', 'HEAD')
if (!$head) { throw "This is not a Git checkout: $root" }
$branch = Invoke-Git @('rev-parse', '--abbrev-ref', 'HEAD')
$dirty = [bool](Invoke-Git @('status', '--porcelain'))
$origin = Invoke-Git @('rev-parse', 'refs/remotes/origin/main')

$version = $null
try { $version = (Get-Content (Join-Path $root 'version.json') -Raw | ConvertFrom-Json).version } catch {}

$stamp = $null
$stampPath = Join-Path $root 'alibi/build-info.json'
if (Test-Path $stampPath) {
  try { $stamp = Get-Content $stampPath -Raw | ConvertFrom-Json } catch {}
}

$running = $null
$health = $null
try {
  $health = Invoke-RestMethod -Uri ($Url.TrimEnd('/') + '/api/health') -TimeoutSec 3
  $running = $health.build
} catch {}

$problems = 0
$unknown = 0
$hints = @()

$repoLine = 'Repository  {0} ({1}{2})' -f (Format-Sha $head), $branch, $(if ($dirty) { ', uncommitted changes' } else { '' })
Write-Host ''
Write-Host ("Alibi version {0}" -f $(if ($version) { $version } else { 'unknown' })) -ForegroundColor Cyan
Write-Host $repoLine
Write-Host ''

if ($origin) {
  if ($origin -eq $head) {
    Write-Row 'GitHub' ("origin/main {0}" -f (Format-Sha $origin)) 'match' 'Green'
  } else {
    $ahead = 0
    $behind = 0
    $counts = Invoke-Git @('rev-list', '--left-right', '--count', 'origin/main...HEAD')
    if ($counts) {
      $parts = $counts -split '\s+'
      $behind = [int]$parts[0]
      $ahead = [int]$parts[1]
    }
    $problems++
    if ($behind -gt 0) { $hints += 'Repository is behind GitHub -> git pull --ff-only' }
    if ($ahead -gt 0) { $hints += 'Repository is ahead of GitHub -> git push origin main' }
    if ($behind -eq 0 -and $ahead -eq 0) { $hints += 'Branches diverged -> reconcile local and origin/main' }
    Write-Row 'GitHub' ("origin/main {0}" -f (Format-Sha $origin)) ("{0} behind, {1} ahead" -f $behind, $ahead) 'Yellow'
  }
} else {
  $unknown++
  Write-Row 'GitHub' 'origin/main not available' 'run without -Offline' 'Yellow'
}

if (!$stamp) {
  $unknown++
  Write-Row 'Build stamp' 'alibi/build-info.json missing' 'run the frontend build' 'Yellow'
} elseif ($stamp.commit -eq $head) {
  Write-Row 'Build stamp' ("{0} @ {1}" -f $stamp.version, (Format-Sha $stamp.commit)) 'match' 'Green'
} else {
  $problems++
  $hints += 'Build stamp is stale -> npm --prefix alibi/frontend run build'
  Write-Row 'Build stamp' ("{0} @ {1}" -f $stamp.version, (Format-Sha $stamp.commit)) ("stale, repo is {0}" -f (Format-Sha $head)) 'Yellow'
}

if (!$health) {
  $unknown++
  Write-Row 'Running app' ("{0} not reachable" -f $Url) 'start Alibi to check' 'Yellow'
} elseif (!$running) {
  $problems++
  $hints += 'Running app predates version reporting -> reinstall Alibi'
  Write-Row 'Running app' 'no build information' 'pre-0.2.0 install, reinstall' 'Yellow'
} elseif ($running.commit -eq $head -and $running.version -eq $version) {
  Write-Row 'Running app' ("v{0} @ {1}" -f $running.version, (Format-Sha $running.commit)) 'match' 'Green'
} else {
  $problems++
  $hints += 'Running app is stale -> .\alibi\Stop-Alibi.ps1, then .\alibi\Launch-Alibi.ps1 (or reinstall)'
  Write-Row 'Running app' ("v{0} @ {1}" -f $running.version, (Format-Sha $running.commit)) ("stale, repo is {0}" -f (Format-Sha $head)) 'Yellow'
}

Write-Host ''
if ($problems -eq 0 -and $unknown -eq 0) {
  Write-Host 'Up to date: repository, GitHub, build stamp, and running app all match.' -ForegroundColor Green
  exit 0
}
if ($problems -gt 0) {
  Write-Host 'Not up to date:' -ForegroundColor Yellow
  foreach ($hint in $hints) { Write-Host "  $hint" }
  exit 1
}
Write-Host 'Inconclusive: start Alibi and rerun, or rerun without -Offline to fetch GitHub.' -ForegroundColor Yellow
exit 2
