<#
.SYNOPSIS
    Feedback-loop harness for the "Creator pops up many times" bug.

.DESCRIPTION
    Launches N copies of the frozen exe (simulating rapid double-clicks) and
    checks that only ONE instance survives (single-instance guard works).

    This is the red/green loop from DEBUGGING_PROTOCOL.md:
      - RED  (non-zero exit): bug reproduced -> steady-state window count > expected.
      - GREEN (exit 0)      : fixed -> every iteration settles to exactly one window.

    We RAISE the reproduction rate (more concurrent launches) until the bug fires
    in >5% of runs, which proves the loop is trustworthy before we call it fixed.

.PARAMETER Exe
    Path to the frozen Creator executable to test.

.PARAMETER Launches
    How many copies to spawn per iteration (the stress that amplifies the race).
    Default 8.

.PARAMETER Iterations
    How many times to repeat the launch sequence. Default 100.

.PARAMETER StaggerMs
    Delay between launches within an iteration (ms). Smaller = harsher race.
    Default 30.

.PARAMETER SettleSec
    How long to watch process count after launching, before judging steady-state.
    Default 12.

.PARAMETER ExpectedProc
    Expected steady-state process count for a single window.
      1 = --onedir on Windows (single process)
      2 = --onefile        (bootloader + app)
    Default 1.
#>
[CmdletBinding()]
param(
    [string] $Exe = "dist\Creator\Creator.exe",
    [int]    $Launches = 8,
    [int]    $Iterations = 100,
    [int]    $StaggerMs = 30,
    [int]    $SettleSec = 12,
    [int]    $ExpectedProc = 1
)

$ErrorActionPreference = "Stop"
$Exe = Resolve-Path $Exe -ErrorAction Stop
Write-Host "audit_spawn: exe=$Exe launches/iter=$Launches iterations=$Iterations stagger=${StaggerMs}ms settle=${SettleSec}s expectedProc=$ExpectedProc"

# Baseline: kill any leftovers from a previous run.
Get-Process -Name "Creator" -ErrorAction SilentlyContinue | Stop-Process -Force

$failures = 0
$maxPeak = 0
$timeline = @()

for ($it = 1; $it -le $Iterations; $it++) {
    # Launch Launches copies with a small stagger (the double-click race).
    for ($i = 0; $i -lt $Launches; $i++) {
        Start-Process -FilePath $Exe
        if ($StaggerMs -gt 0) { Start-Sleep -Milliseconds $StaggerMs }
    }

    # Sample process count; track the peak and the steady-state (final) value.
    $peak = 0
    $samples = $SettleSec * 4   # 250ms cadence
    for ($s = 0; $s -lt $samples; $s++) {
        Start-Sleep -Milliseconds 250
        $c = (Get-Process -Name "Creator" -ErrorAction SilentlyContinue).Count
        if ($c -gt $peak) { $peak = $c }
    }
    $final = (Get-Process -Name "Creator" -ErrorAction SilentlyContinue).Count
    if ($peak -gt $maxPeak) { $maxPeak = $peak }

    $bug = $final -gt $ExpectedProc
    if ($bug) { $failures++ }
    $timeline += [pscustomobject]@{
        Iteration = $it
        Peak      = $peak
        Final     = $final
        Bug       = $bug
    }
    # Clean up so the next iteration starts from a known state.
    Get-Process -Name "Creator" -ErrorAction SilentlyContinue | Stop-Process -Force
}

$rate = [math]::Round(($failures / $Iterations) * 100, 1)
Write-Host ""
Write-Host "=== audit_spawn result ==="
Write-Host "iterations : $Iterations"
Write-Host "failures   : $failures"
Write-Host "fail rate  : $rate%  (red-capable loop requires >5% to be trustworthy)"
Write-Host "max peak   : $maxPeak processes"
# Show the first few iterations as a sample timeline.
$timeline | Select-Object -First 10 | ForEach-Object { "  it$($_.Iteration): peak=$($_.Peak) final=$($_.Final) bug=$($_.Bug)" }

if ($failures -eq 0) {
    Write-Host "VERDICT: GREEN (0% failure) - single-instance guard holds."
    exit 0
} else {
    Write-Host "VERDICT: RED ($rate% failure) - bug reproduced; loop is trustworthy."
    exit 1
}
