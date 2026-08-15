<#
.SYNOPSIS
    One-line installer for Creator (the no-code app builder), opencode-style.

.DESCRIPTION
    Downloads the latest standalone Creator binary from GitHub Releases and
    installs it to a folder on your PATH. No Python required.

    Usage (copy/paste into PowerShell):
        irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex

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

$asset = $release.assets | Where-Object { $_.name -like "Creator*.exe" } | Select-Object -First 1
if (-not $asset) {
    Write-Error "No Creator.exe found in the latest release of $Repo. Build it with 'python build_exe.py' and upload to Releases."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$dest = Join-Path $InstallDir "Creator.exe"
Write-Host "Downloading $($asset.name) ..."
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -UseBasicParsing

$current = [Environment]::GetEnvironmentVariable("Path", "User")
if ($current -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$current;$InstallDir", "User")
    Write-Host "Added $InstallDir to your PATH."
}

Write-Host "`nDone! Restart your terminal and run:  Creator"
