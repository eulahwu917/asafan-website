# scripts/deploy.ps1
# Mirror the project root to Locaweb shared hosting via FTPS.
#
# Usage:
#   First run (find the doc root):
#     powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 -Action discover
#
#   Then upload (after we know the doc root):
#     powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 -Action upload -TargetRoot "/home/asafan2/web/"
#
#   Preview without uploading:
#     powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 -Action upload -TargetRoot "/home/asafan2/web/" -DryRun

[CmdletBinding()]
param(
  [ValidateSet('discover','upload')]
  [string]$Action = 'discover',
  [string]$FtpHost = 'ftp.asafan2.hospedagemdesites.ws',
  [int]$FtpPort = 21,
  [string]$FtpUser = 'asafan2',
  [string]$TargetRoot = '/home/asafan2/',
  [switch]$DryRun,
  [switch]$NoTls
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# Exclude these from upload (top-level names and any subpath segments)
$ExcludeNames = @(
  '.git', '.gitignore', '.gitattributes',
  '.claude', '.gstack', '.vscode',
  'sessions', 'raw_assets', 'project files', 'assets_upgrade',
  # docs/ holds internal client feedback files, not site content — must never go to a public URL
  'docs',
  'scripts',
  'PROJECT.md', 'REFERENCE.md',
  # deploy artifacts (built locally, not part of the live site)
  'deploy.zip', 'test.zip', 'hero-video-payload.bin',
  # mail-config.php must NEVER be uploaded into public_html/ — it lives at /home/asafan2/ (one level above), gets there manually via web file manager
  'mail-config.php',
  # mail-config.example.php is fine to upload (template, no secrets), keeps file alongside submit.php for reference
  # _diag.php is the temporary mail() probe — remove from server after debugging
  '_diag.php'
)

function Get-PlainPassword {
  $secure = Read-Host -Prompt "FTP password for $FtpUser@$FtpHost" -AsSecureString
  if ($secure.Length -eq 0) { throw "No password entered." }
  $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
  } finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function New-FtpRequest {
  param([string]$Uri, [string]$Method)
  $req = [System.Net.FtpWebRequest]::Create($Uri)
  $req.Method = $Method
  $req.Credentials = New-Object System.Net.NetworkCredential($script:User, $script:Pass)
  $req.EnableSsl = (-not $NoTls)
  $req.UsePassive = $true
  $req.UseBinary = $true
  $req.KeepAlive = $true
  $req.Timeout = 60000
  return $req
}

function Invoke-FtpList {
  param([string]$RemotePath)
  $uri = "ftp://${FtpHost}:${FtpPort}${RemotePath}"
  $req = New-FtpRequest -Uri $uri -Method ([System.Net.WebRequestMethods+Ftp]::ListDirectoryDetails)
  $resp = $req.GetResponse()
  $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
  $text = $reader.ReadToEnd()
  $reader.Close(); $resp.Close()
  return ($text.TrimEnd("`r","`n") -split "`r?`n")
}

function Invoke-FtpMakeDir {
  param([string]$RemotePath)
  $uri = "ftp://${FtpHost}:${FtpPort}${RemotePath}"
  $req = New-FtpRequest -Uri $uri -Method ([System.Net.WebRequestMethods+Ftp]::MakeDirectory)
  try {
    $resp = $req.GetResponse(); $resp.Close()
  } catch [System.Net.WebException] {
    # Best-effort: directory-already-exists is expected on every re-deploy (this host doesn't
    # always return the standard 550 for that case, sometimes a generic 500 instead), and a
    # genuinely missing/bad path will surface loudly on the file upload that follows anyway.
    $ftpResp = $_.Exception.Response -as [System.Net.FtpWebResponse]
    $code = if ($ftpResp) { $ftpResp.StatusCode } else { '(no response)' }
    Write-Host "  (mkdir $RemotePath -> $code, continuing)" -ForegroundColor DarkGray
  }
}

function Invoke-FtpUpload {
  param([string]$RemotePath, [string]$LocalFile)
  $uri = "ftp://${FtpHost}:${FtpPort}${RemotePath}"
  $req = New-FtpRequest -Uri $uri -Method ([System.Net.WebRequestMethods+Ftp]::UploadFile)
  $bytes = [System.IO.File]::ReadAllBytes($LocalFile)
  $req.ContentLength = $bytes.Length
  $stream = $req.GetRequestStream()
  $stream.Write($bytes, 0, $bytes.Length)
  $stream.Close()
  $resp = $req.GetResponse(); $resp.Close()
}

# ----- main -----
$script:User = $FtpUser
$script:Pass = Get-PlainPassword

Write-Host ""
Write-Host "Host:   ${FtpHost}:${FtpPort}  (FTPS: $(-not $NoTls))" -ForegroundColor Cyan
Write-Host "User:   $FtpUser" -ForegroundColor Cyan
Write-Host "Target: $TargetRoot" -ForegroundColor Cyan
Write-Host ""

if ($Action -eq 'discover') {
  Write-Host "Listing $TargetRoot ..." -ForegroundColor Yellow
  $lines = Invoke-FtpList -RemotePath $TargetRoot
  $lines | ForEach-Object { Write-Host "  $_" }
  Write-Host ""
  Write-Host "Look for a directory named: web/  public_html/  www/  htdocs/" -ForegroundColor Green
  Write-Host "That's the web doc root. Next:"
  Write-Host "  .\scripts\deploy.ps1 -Action upload -TargetRoot '/home/asafan2/<docroot>/'"
  return
}

# upload mode
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$allFiles = Get-ChildItem -Path $repoRoot -Recurse -File
$filtered = @($allFiles | Where-Object {
  $rel = $_.FullName.Substring($repoRoot.Length).TrimStart('\','/')
  $segs = $rel -split '[\\/]'
  $excluded = $false
  foreach ($name in $ExcludeNames) {
    if ($segs -contains $name) { $excluded = $true; break }
  }
  -not $excluded
})

$totalBytes = ($filtered | Measure-Object Length -Sum).Sum
Write-Host "Files to upload: $($filtered.Count)" -ForegroundColor Yellow
Write-Host "Total size:      $([Math]::Round($totalBytes / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
  $filtered | ForEach-Object {
    $rel = ($_.FullName.Substring($repoRoot.Length).TrimStart('\','/')) -replace '\\','/'
    Write-Host "  $rel  ($([Math]::Round($_.Length/1KB,1)) KB)"
  }
  Write-Host ""
  Write-Host "DRY RUN - no files uploaded." -ForegroundColor Magenta
  return
}

$confirm = Read-Host "Upload to $TargetRoot ? [y/N]"
if ($confirm.ToLower() -ne 'y') { Write-Host "Cancelled."; return }

# Create remote directories (parent chains, idempotent)
$remoteDirs = @($filtered | ForEach-Object {
  $rel = ($_.FullName.Substring($repoRoot.Length).TrimStart('\','/')) -replace '\\','/'
  $relDir = Split-Path $rel -Parent
  if ($relDir) { ($relDir -replace '\\','/') } else { '' }
} | Where-Object { $_ } | Select-Object -Unique | Sort-Object)

Write-Host "Ensuring $($remoteDirs.Count) directories exist..." -ForegroundColor Cyan
$createdDirs = New-Object System.Collections.Generic.HashSet[string]
foreach ($d in $remoteDirs) {
  $parts = $d -split '/'
  $accum = $TargetRoot.TrimEnd('/')
  foreach ($p in $parts) {
    $accum = "$accum/$p"
    if (-not $createdDirs.Contains($accum)) {
      Invoke-FtpMakeDir -RemotePath $accum
      [void]$createdDirs.Add($accum)
    }
  }
}

# Upload
$i = 0
$sw = [Diagnostics.Stopwatch]::StartNew()
foreach ($f in $filtered) {
  $i++
  $rel = ($f.FullName.Substring($repoRoot.Length).TrimStart('\','/')) -replace '\\','/'
  $remotePath = "$($TargetRoot.TrimEnd('/'))/$rel"
  Write-Progress -Activity "Uploading to $FtpHost" -Status "$i / $($filtered.Count): $rel" -PercentComplete (($i / $filtered.Count) * 100)
  try {
    Invoke-FtpUpload -RemotePath $remotePath -LocalFile $f.FullName
  } catch {
    Write-Host "FAILED: $rel - $($_.Exception.Message)" -ForegroundColor Red
    throw
  }
}
Write-Progress -Activity "Uploading" -Completed
$sw.Stop()
Write-Host ""
Write-Host "Done. Uploaded $($filtered.Count) files in $([Math]::Round($sw.Elapsed.TotalSeconds,1))s." -ForegroundColor Green
