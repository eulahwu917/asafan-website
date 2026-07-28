# scripts/deploy-curl.ps1
# Mirror the project root to Locaweb shared hosting via FTPS, using curl.exe instead of
# System.Net.FtpWebRequest (see scripts/deploy.ps1). FtpWebRequest's explicit-FTPS handshake
# doesn't play nice with this host - every command (MKD *and* STOR) came back "500 Syntax
# error, command unrecognized" once the session got into that state. curl's FTPS
# implementation is far more standards-compliant; use this script instead.
#
# Usage:
#   Dry run (no upload, just lists what would go):
#     powershell -ExecutionPolicy Bypass -File .\scripts\deploy-curl.ps1 -DryRun
#
#   Real upload:
#     powershell -ExecutionPolicy Bypass -File .\scripts\deploy-curl.ps1

[CmdletBinding()]
param(
  [string]$FtpHost = 'ftp.asafan2.hospedagemdesites.ws',
  [int]$FtpPort = 21,
  [string]$FtpUser = 'asafan2',
  [string]$TargetRoot = '/public_html/',
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$curlCmd = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curlCmd) {
  throw "curl.exe not found on PATH. Windows 10/11 ships it at C:\Windows\System32\curl.exe by default - check your PATH."
}

# Same exclude list as deploy.ps1 - keep the two in sync if either changes.
$ExcludeNames = @(
  '.git', '.gitignore', '.gitattributes',
  '.claude', '.gstack', '.vscode',
  'sessions', 'raw_assets', 'project files', 'assets_upgrade',
  # docs/ holds internal client feedback files, not site content - must never go to a public URL
  'docs',
  'scripts',
  'PROJECT.md', 'REFERENCE.md',
  'deploy.zip', 'test.zip', 'hero-video-payload.bin',
  'mail-config.php',
  '_diag.php'
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$allFiles = Get-ChildItem -Path $repoRoot -Recurse -File
$filtered = @($allFiles | Where-Object {
  $rel = $_.FullName.Substring($repoRoot.Length).TrimStart('\', '/')
  $segs = $rel -split '[\\/]'
  $excluded = $false
  foreach ($name in $ExcludeNames) {
    if ($segs -contains $name) { $excluded = $true; break }
  }
  -not $excluded
})

$totalBytes = ($filtered | Measure-Object Length -Sum).Sum
Write-Host ""
Write-Host "Host:   ${FtpHost}:${FtpPort}  (FTPS via curl)" -ForegroundColor Cyan
Write-Host "User:   $FtpUser" -ForegroundColor Cyan
Write-Host "Target: $TargetRoot" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files to upload: $($filtered.Count)" -ForegroundColor Yellow
Write-Host "Total size:      $([Math]::Round($totalBytes / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
  $filtered | ForEach-Object {
    $rel = ($_.FullName.Substring($repoRoot.Length).TrimStart('\', '/')) -replace '\\', '/'
    Write-Host "  $rel  ($([Math]::Round($_.Length / 1KB, 1)) KB)"
  }
  Write-Host ""
  Write-Host "DRY RUN - no files uploaded." -ForegroundColor Magenta
  return
}

$confirm = Read-Host "Upload $($filtered.Count) files to $TargetRoot via curl? [y/N]"
if ($confirm.ToLower() -ne 'y') { Write-Host "Cancelled."; return }

$secure = Read-Host -Prompt "FTP password for $FtpUser@$FtpHost" -AsSecureString
if ($secure.Length -eq 0) { throw "No password entered." }
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$plainPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

# Credentials go in a temp curl config file, never on the visible command line / process list.
$configPath = [System.IO.Path]::GetTempFileName()
"user = `"${FtpUser}:${plainPass}`"" | Out-File -FilePath $configPath -Encoding ASCII -NoNewline
$plainPass = $null

try {
  $i = 0
  $failed = @()
  $sw = [Diagnostics.Stopwatch]::StartNew()
  foreach ($f in $filtered) {
    $i++
    $rel = ($f.FullName.Substring($repoRoot.Length).TrimStart('\', '/')) -replace '\\', '/'
    $remoteUrl = "ftp://${FtpHost}:${FtpPort}$($TargetRoot.TrimEnd('/'))/$rel"
    Write-Progress -Activity "Uploading to $FtpHost (curl)" -Status "$i / $($filtered.Count): $rel" -PercentComplete (($i / $filtered.Count) * 100)

    & curl.exe -K $configPath --ssl-reqd --ftp-create-dirs -T "$($f.FullName)" "$remoteUrl" --silent --show-error
    if ($LASTEXITCODE -ne 0) {
      Write-Host "FAILED: $rel (curl exit $LASTEXITCODE)" -ForegroundColor Red
      $failed += $rel
    }
  }
  Write-Progress -Activity "Uploading" -Completed
  $sw.Stop()
  Write-Host ""
  if ($failed.Count -eq 0) {
    Write-Host "Done. Uploaded $($filtered.Count) files in $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s." -ForegroundColor Green
  }
  else {
    Write-Host "Finished with $($failed.Count) failure(s) out of $($filtered.Count):" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
  }
}
finally {
  Remove-Item -Path $configPath -Force -ErrorAction SilentlyContinue
}
