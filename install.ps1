<#
.SYNOPSIS
    One-line installer for Creator (the no-code app builder), opencode-style.

.DESCRIPTION
    Downloads the latest standalone Creator build from GitHub Releases and
    installs it to a folder on your PATH. No Python required.

    The release publishes an onedir build archived as Creator-<os>.zip
    (a folder containing Creator.exe), optionally accompanied by a
    Creator-<os>.sha256 checksum file.

    Usage (copy/paste into PowerShell):
        irm https://raw.githubusercontent.com/thewi/Creator/main/install.ps1 | iex

.PARAMETER Repo
    GitHub "owner/name" hosting Creator. Defaults to "thewi/Creator".

.PARAMETER InstallDir
    Where to install. Defaults to "$env:LOCALAPPDATA\Programs\Creator".
#>

[CmdletBinding()]
param(
    [string] $Repo = "thewi/Creator",
    [string] $InstallDir = "$env:LOCALAPPDATA\Programs\Creator"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing Creator from $Repo ..."

$release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" `
    -Headers @{ Accept = "application/vnd.github+json" }

# Prefer the onedir zip; fall back to a bare exe.
$asset = $release.assets | Where-Object { $_.name -like "Creator*.zip" } | Select-Object -First 1
if (-not $asset) {
    $asset = $release.assets | Where-Object { $_.name -like "Creator*.exe" } | Select-Object -First 1
}
if (-not $asset) {
    Write-Error "No Creator build found in the latest release of $Repo. Build it with 'python build_exe.py' and upload to Releases."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$tmpFile = Join-Path $env:TEMP $asset.name
Write-Host "Downloading $($asset.name) ..."
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $tmpFile -UseBasicParsing

# Best-effort checksum verification against a companion *.sha256 asset.
$shaAsset = $release.assets | Where-Object { $_.name -like "$($asset.BaseName)*.sha256" } | Select-Object -First 1
if ($shaAsset) {
    $expected = (Invoke-RestMethod -Uri $shaAsset.browser_download_url).Trim().Split()[0]
    $actual = (Get-FileHash -Algorithm SHA256 $tmpFile).Hash
    if ($actual -ne $expected) {
        Write-Error "Checksum mismatch for $($asset.name): expected $expected, got $actual"
    }
    Write-Host "Checksum verified."
}

if ($asset.name -like "*.zip") {
    Expand-Archive -Path $tmpFile -DestinationPath $InstallDir -Force
    # The onedir archive extracts into a 'Creator' subfolder; flatten it.
    $inner = Join-Path $InstallDir "Creator"
    if (Test-Path (Join-Path $inner "Creator.exe")) {
        Get-ChildItem $inner | Move-Item -Destination $InstallDir -Force
        Remove-Item $inner -Recurse -Force
    }
    $dest = Join-Path $InstallDir "Creator.exe"
} else {
    Move-Item -Path $tmpFile -Destination (Join-Path $InstallDir "Creator.exe") -Force
    $dest = Join-Path $InstallDir "Creator.exe"
}

$current = [Environment]::GetEnvironmentVariable("Path", "User")
if ($current -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$current;$InstallDir", "User")
    Write-Host "Added $InstallDir to your PATH."
}

Write-Host "`nDone! Restart your terminal and run:  Creator"
