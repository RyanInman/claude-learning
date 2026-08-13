<#
Start the deck design studio on Windows. Runs in the foreground - Ctrl-C stops it.
Run it from the project root; specs resolve against your current directory.

  <skill>\scripts\studio.ps1                     # the only deck under decks\
  <skill>\scripts\studio.ps1 <deck-name>         # decks\<deck-name>\<deck-name>-spec.yaml
  <skill>\scripts\studio.ps1 path\to\spec.yaml   # any spec by path
  $env:PORT = 4322; <skill>\scripts\studio.ps1   # a different port

Nothing is written to disk until you press Save + build in the browser.
#>

[CmdletBinding()]
param([string]$Spec)

$ErrorActionPreference = 'Stop'

if (-not $Spec) {
  # No argument: fine when the project has exactly one deck, ambiguous otherwise.
  # A leading underscore (decks\_archive) marks a directory that is not a deck.
  $decks = @(Get-ChildItem -Path 'decks' -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike '_*' })
  if ($decks.Count -eq 1) {
    $Spec = $decks[0].Name
  } else {
    Write-Error "Name a deck. Available:`n$($decks.Name -join "`n")"
    exit 1
  }
}

# A bare deck name is shorthand for that deck's spec.
if ($Spec -notmatch '[\\/]') { $Spec = "decks\$Spec\$Spec-spec.yaml" }

$port = if ($env:PORT) { [int]$env:PORT } else { 4321 }
$studio = Join-Path $PSScriptRoot 'studio.js'

if (-not (Test-Path -LiteralPath $Spec -PathType Leaf)) {
  Write-Error "No such spec: $Spec"
  exit 1
}

# A studio left over from an earlier session holds a stale copy of the spec in
# memory, and saving from it would overwrite the current file. Clear it out.
$listening = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
foreach ($procId in ($listening.OwningProcess | Select-Object -Unique)) {
  Write-Host "Stopping the studio already on port $port (pid $procId)"
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}
if ($listening) { Start-Sleep -Seconds 1 }

$url = "http://127.0.0.1:$port"
Start-Job -ScriptBlock {
  param($u)
  Start-Sleep -Seconds 2
  Start-Process $u
} -ArgumentList $url | Out-Null

& node $studio $Spec --port $port
exit $LASTEXITCODE
