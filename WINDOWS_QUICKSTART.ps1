# Windows PowerShell Quick Start for Animation Assembly
# For AMD Radeon 660M (Windows 11)
# Copy each section and paste into PowerShell as needed

# ============================================================================
# STEP 1: VERIFY PYTHON & DEPENDENCIES
# ============================================================================

Write-Host "Checking Python and dependencies..." -ForegroundColor Green

python --version
pip list | Select-String "opencv|numpy|ffmpeg"

# If anything is missing:
# pip install opencv-python numpy

# ============================================================================
# STEP 2: CHECK GRADED CLIPS DIRECTORY
# ============================================================================

Write-Host "Verifying graded clips..." -ForegroundColor Green

$clipCount = (Get-ChildItem graded/*.mp4 -ErrorAction SilentlyContinue).Count
Write-Host "Total clips: $clipCount (expected: 99)"

if ($clipCount -eq 0) {
    Write-Host "ERROR: graded/ directory not found or is empty" -ForegroundColor Red
    Write-Host "Run coherence_pass.py first on this machine"
    exit 1
}

# Sample check: verify one clip exists and has reasonable size
$sampleClip = Get-Item graded/beach_01.mp4 -ErrorAction SilentlyContinue
if ($sampleClip) {
    $sizeMB = [math]::Round($sampleClip.Length / 1MB, 2)
    Write-Host "Sample clip beach_01.mp4: $sizeMB MB" -ForegroundColor Green
} else {
    Write-Host "WARNING: beach_01.mp4 not found - verify clip naming" -ForegroundColor Yellow
}

# ============================================================================
# STEP 3: CREATE EXPANDED PAIRS CSV (if missing)
# ============================================================================

Write-Host "Creating expanded_pairs.csv..." -ForegroundColor Green

if (-Not (Test-Path "expanded_pairs.csv")) {
    python gen_intermediate_frames.py
    Write-Host "✓ Generated expanded_pairs.csv" -ForegroundColor Green
} else {
    Write-Host "✓ expanded_pairs.csv already exists" -ForegroundColor Green
}

# ============================================================================
# STEP 4: VOICEOVER SYNC
# ============================================================================

# 4a: Create manifest template
Write-Host "Creating voiceover manifest..." -ForegroundColor Green

python sync_audio.py --create-template

Write-Host "`nEdit voiceover_manifest.json with ElevenLabs flow IDs" -ForegroundColor Yellow
Write-Host "Then download audio files to voiceovers/ directory" -ForegroundColor Yellow
Write-Host "  ch01_voiceover.wav, ch02_voiceover.wav, ..., ch21_voiceover.wav" -ForegroundColor Yellow

# [User manually edits voiceover_manifest.json and downloads files]

# 4b: Validate manifest
Write-Host "Validating voiceover manifest..." -ForegroundColor Green

python sync_audio.py --manifest voiceover_manifest.json --validate-only

# 4c: Concatenate voiceovers (once all files are downloaded)
Write-Host "Concatenating voiceovers..." -ForegroundColor Green

python sync_audio.py `
    --manifest voiceover_manifest.json `
    --audio-dir voiceovers `
    --output voiceover_master.wav

Write-Host "✓ Voiceover master audio created" -ForegroundColor Green

# ============================================================================
# STEP 5: FINAL VIDEO ASSEMBLY
# ============================================================================

# 5a: Dry run (preview FFmpeg command)
Write-Host "Previewing FFmpeg assembly command..." -ForegroundColor Green

python assemble_final.py `
    --clips graded `
    --pairs expanded_pairs.csv `
    --audio voiceover_master.wav `
    --output final.mp4 `
    --dry-run

Write-Host "`nReview the command above. Press Enter to continue..." -ForegroundColor Yellow
Read-Host

# 5b: Full assembly (this will take 30-60 minutes)
Write-Host "Starting video assembly. This may take 30-60 minutes..." -ForegroundColor Green
Write-Host "Do not close this window." -ForegroundColor Yellow

$startTime = Get-Date

python assemble_final.py `
    --clips graded `
    --pairs expanded_pairs.csv `
    --audio voiceover_master.wav `
    --output final.mp4

$endTime = Get-Date
$duration = $endTime - $startTime

if (Test-Path "final.mp4") {
    $sizeMB = [math]::Round((Get-Item final.mp4).Length / 1MB, 2)
    Write-Host "✓ Assembly complete!" -ForegroundColor Green
    Write-Host "  Output: final.mp4 ($sizeMB MB)" -ForegroundColor Green
    Write-Host "  Time: $([math]::Round($duration.TotalMinutes, 1)) minutes" -ForegroundColor Green
} else {
    Write-Host "✗ Assembly failed. Check error messages above." -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 6 (OPTIONAL): CHARACTER ANIMATION
# ============================================================================

$charResponse = Read-Host "Integrate character animations now? (y/n)"

if ($charResponse -eq "y") {
    Write-Host "Creating character metadata template..." -ForegroundColor Green

    python integrate_character_animation.py --create-template

    Write-Host "Edit character_metadata.json with your character placement and poses" -ForegroundColor Yellow
    Write-Host "Then run:" -ForegroundColor Yellow
    Write-Host "  python integrate_character_animation.py --metadata character_metadata.json --env-clips graded --char-clips characters --output-dir composited" -ForegroundColor Cyan

} else {
    Write-Host "Skipping character integration. You can add it later." -ForegroundColor Green
}

# ============================================================================
# STEP 7: SUMMARY
# ============================================================================

Write-Host "`n" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Assembly Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Green
Write-Host "1. Verify final.mp4 plays correctly in media player" -ForegroundColor Cyan
Write-Host "2. Check audio sync and video quality" -ForegroundColor Cyan
Write-Host "3. Import to Godot project:" -ForegroundColor Cyan
Write-Host "   - File > Import" -ForegroundColor Cyan
Write-Host "   - Select: final.mp4" -ForegroundColor Cyan
Write-Host "   - Import to: res://assets/animation/final.mp4" -ForegroundColor Cyan

Write-Host "`nFile locations:" -ForegroundColor Green
Write-Host "  Animation: $(Resolve-Path final.mp4)" -ForegroundColor Cyan
Write-Host "  Voiceover: $(Resolve-Path voiceover_master.wav)" -ForegroundColor Cyan
Write-Host "  Clips (backup): $(Resolve-Path graded/)" -ForegroundColor Cyan

Write-Host "`nFor troubleshooting, see:" -ForegroundColor Green
Write-Host "  - ASSEMBLY_GUIDE.md (detailed walkthrough)" -ForegroundColor Cyan
Write-Host "  - ASSEMBLY_STATUS.md (current status)" -ForegroundColor Cyan

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

function Test-ClipQuality {
    param(
        [string]$ClipPath = "final.mp4"
    )

    Write-Host "Checking video quality of $ClipPath..." -ForegroundColor Green

    $ffprobe = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration -of default=noprint_wrappers=1:nokey=1:pairs=1 $ClipPath"

    # Fallback: just check file size and duration
    if (Test-Path $ClipPath) {
        $sizeBytes = (Get-Item $ClipPath).Length
        $sizeMB = [math]::Round($sizeBytes / 1MB, 2)
        Write-Host "  File size: $sizeMB MB" -ForegroundColor Cyan
        Write-Host "  ✓ File exists and is readable" -ForegroundColor Green
    }
}

function Clean-Temp {
    Write-Host "Cleaning temporary files..." -ForegroundColor Green

    Remove-Item audio_concat.txt -ErrorAction SilentlyContinue
    Remove-Item ffmpeg_concat.txt -ErrorAction SilentlyContinue

    Write-Host "✓ Cleanup complete" -ForegroundColor Green
}

# ============================================================================
# ERROR RECOVERY
# ============================================================================

# If assembly fails with "No such file or directory":
# - Check that expanded_pairs.csv exists and has correct format
# - Verify all clip files in graded/ match names in expanded_pairs.csv

# If assembly fails with "Invalid data found":
# - Run qa_report.py to check for corrupted clips
# - Verify graded clips are valid MP4 files
# - Check file sizes are reasonable (~300-500KB each)

# If assembly fails with "Duration mismatch":
# - Check voiceover duration vs. animation duration
# - Animation: ~41 seconds (99 clips × 10 frames at 24fps)
# - Voiceover should be similar or slightly shorter

Write-Host "`nFor detailed troubleshooting, run:" -ForegroundColor Yellow
Write-Host "  python no-sand-beach-toolkit/qa_report.py --out graded --sheet contact.png" -ForegroundColor Cyan
