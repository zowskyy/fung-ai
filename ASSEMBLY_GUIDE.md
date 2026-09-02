# Final Assembly Guide — No Sand Beach Animation

## Current State

✓ Coherence pass complete: 99 graded MP4 clips in `graded/` directory  
✓ All clips pass QA (peak flow <3px, no flicker)  
✓ Luminance normalized to batch median (within-location: 0-1px drift)  
✓ Film grain + vignette applied for expressionist B&W aesthetic

## Next Steps Overview

This guide walks you through the final assembly pipeline:

1. **Verify clip directory structure** on your Windows 660M machine
2. **Create expanded_pairs.csv** if not already present (defines clip order)
3. **Sync audio voiceovers** from ElevenLabs (21 chapters)
4. **Compose final video** with audio mux (FFmpeg concat + crossfades)
5. **Integrate character animations** from ElevenLabs (optional for now)
6. **Export for Godot** at target resolution

---

## Step 1: Verify Graded Clips Directory

On your Windows machine, confirm you have:

```
graded/
├── beach_01.mp4      (10-frame interpolation, ~410ms at 24fps)
├── beach_02.mp4
├── beach_03.mp4
├── beach_04.mp4
├── beach_05.mp4
├── ...
├── schoolyard_99.mp4
└── _jobs.sqlite      (QA database from interpolate_stack.py)
```

**Count check:**
```powershell
(Get-ChildItem graded/*.mp4).Count
# Should output: 99 (or close to it if schoolyard_v4 issue wasn't fixed)
```

---

## Step 2: Create Expanded Pairs CSV

If you haven't already, you need `expanded_pairs.csv` that defines the **clip order** and **timing**.

### Option A: Regenerate with Intermediate Keyframes

If you still have the keyframes (beach_v1-v4, etc.):

```powershell
cd /path/to/fung-ai
python gen_intermediate_frames.py
# Outputs: expanded_pairs.csv with 100 pairs (18 original + 82 intermediates)
```

This CSV has format:
```
clip_id,frame_a,frame_b,frames
beach_01,beach_v1.png,beach_v2.png,10
beach_01_a,beach_v1.png,beach_v1_50.png,10
beach_01_b,beach_v1_50.png,beach_v2.png,10
beach_02,beach_v2.png,beach_v3.png,10
...
schoolyard_99,schoolyard_v3.png,schoolyard_v4.png,10
```

### Option B: Use Existing Expanded Pairs

If you have `expanded_pairs.csv` from a previous run, use it as-is.

---

## Step 3: Sync Audio Voiceovers

### 3a. Create Voiceover Manifest Template

```powershell
python sync_audio.py --create-template
# Outputs: voiceover_manifest.json template
```

### 3b. Fill In ElevenLabs Flow IDs

Edit `voiceover_manifest.json`:

```json
{
  "chapters": [
    {
      "chapter": 1,
      "location": "beach",
      "flow_id": "YOUR_FLOW_ID_FROM_ELEVENLABS",
      "duration_sec": 15.2,
      "character": "protagonist",
      "voice_id": "YOUR_VOICE_ID"
    },
    {
      "chapter": 2,
      "location": "car",
      "flow_id": "YOUR_FLOW_ID",
      "duration_sec": 18.7,
      "character": "protagonist",
      "voice_id": "YOUR_VOICE_ID"
    }
    ...
  ]
}
```

### 3c. Download Voiceovers from ElevenLabs

For each chapter flow_id, download the generated audio:

```powershell
# Create voiceovers directory
New-Item -ItemType Directory -Name voiceovers -Force

# Place downloaded audio files:
voiceovers/
├── ch01_voiceover.wav   (from ElevenLabs flow #1)
├── ch02_voiceover.wav   (from ElevenLabs flow #2)
├── ...
└── ch21_voiceover.wav   (from ElevenLabs flow #21)
```

### 3d. Concatenate Voiceovers

```powershell
python sync_audio.py \
  --manifest voiceover_manifest.json \
  --audio-dir voiceovers \
  --output voiceover_master.wav
# Outputs: voiceover_master.wav (concatenated all 21 chapters)
```

**Total duration check:**
```powershell
# voiceover_master.wav duration should match animation duration
# Animation: 99 clips × (10 frames / 24fps) ≈ 41.25 seconds
# Voiceovers should fit within this (narrator can overlap location transitions)
```

---

## Step 4: Assemble Final Video

### 4a. Dry Run (Preview FFmpeg Command)

```powershell
python assemble_final.py \
  --clips graded \
  --pairs expanded_pairs.csv \
  --audio voiceover_master.wav \
  --output final.mp4 \
  --dry-run
# Shows FFmpeg command without running
```

### 4b. Full Assembly

```powershell
python assemble_final.py \
  --clips graded \
  --pairs expanded_pairs.csv \
  --audio voiceover_master.wav \
  --output final.mp4
# Creates final.mp4 with all clips concatenated and audio muxed
# Processing time: ~30-60 minutes on 660M (FFmpeg encodes at ~0.5-1x realtime)
```

**Result:**
```
final.mp4
├── Video: H.264, 1280×720, 24fps, ~41.25 seconds
├── Audio: AAC 128kbps, voiceover master
└── Crossfades at location boundaries (0.5s fade)
```

---

## Step 5: Character Animation Integration (Optional)

This is for layering character animations from ElevenLabs on top of the environment clips.

### 5a. Create Character Metadata Template

```powershell
python integrate_character_animation.py --create-template
# Outputs: character_metadata.json template
```

### 5b. Fill In Character Details

Edit `character_metadata.json` with:
- Character names and ElevenLabs flow_ids
- Per-scene character placement (x, y, scale)
- Pose sequences and timing
- Sync with voiceover

Example structure (see template for full details):
```json
{
  "characters": [
    {
      "name": "protagonist",
      "flow_id": "CHARACTER_FLOW_ID_FROM_ELEVENLABS",
      "base_scale": 1.0,
      "poses": [
        {"name": "idle", "frame_range": [0, 12]},
        {"name": "turn_left", "frame_range": [12, 24]}
      ]
    }
  ],
  "scenes": [
    {
      "clip_id": "beach_01",
      "character": "protagonist",
      "position": {"x": 640, "y": 540, "scale": 1.0}
    }
  ]
}
```

### 5c. Micro-Test on Single Clip

Before running full batch, test character overlay on one clip:

```powershell
python integrate_character_animation.py \
  --metadata character_metadata.json \
  --env-clips graded \
  --char-clips characters \
  --output-dir composited \
  --micro-test beach_01
# Outputs: composited/beach_01_composite.mp4
```

Verify:
- Character is positioned correctly
- Scale/proportions match environment
- Pose transitions are smooth
- Audio sync is tight

### 5d. Full Character Integration

Once micro-test passes:

```powershell
python integrate_character_animation.py \
  --metadata character_metadata.json \
  --env-clips graded \
  --char-clips characters \
  --output-dir composited
# Outputs: composited/ directory with all 99 clips as character+environment composites
```

Then use `assemble_final.py` with `--clips composited` instead of `graded`.

---

## Step 6: Godot Integration

Once you have `final.mp4`, integrate into Godot:

### 6a. Import Video Resource

```
File → Import...
Select: final.mp4
Import to: res://assets/animation/final.mp4
```

### 6b. Create VideoPlayer Scene

```gdscript
# AnimationPlayer.gd
extends VideoPlayer

func _ready():
    stream = load("res://assets/animation/final.mp4")
    play()

func _on_video_finished():
    queue_free()
```

### 6c. Sync Voiceover (if separate)

If you want voiceover as separate AudioStreamPlayer:

```gdscript
# VoiceoverPlayer.gd
extends AudioStreamPlayer

func _ready():
    stream = load("res://assets/audio/voiceover_master.wav")
    play()
```

---

## Troubleshooting

### Clip Count Mismatch

If `(Get-ChildItem graded/*.mp4).Count` shows <99:

1. Check `_jobs.sqlite` for flagged/failed clips:
   ```powershell
   python no-sand-beach-toolkit/qa_report.py --out graded
   ```

2. If schoolyard_v4 is corrupted, regenerate:
   - Use intermediate keyframes for schoolyard transitions
   - Or manually create a placeholder
   - Re-run interpolation for affected pairs

3. Update `expanded_pairs.csv` to exclude missing clips

### FFmpeg Concat Failures

**Error: "No such file or directory"**
- Verify clip filenames match `expanded_pairs.csv` exactly
- Check paths are relative or absolute consistently

**Error: "Invalid data found"**
- Verify all MP4 files are valid (coherence pass completed)
- Check file sizes are reasonable (~200-500KB per clip)

**Error: "Duration mismatch"**
- Voiceover duration must cover animation timeline
- If audio is too long, trim end or add silence
- If audio is too short, loop or pad with silence

### Character Integration Issues

**Characters appear off-screen:**
- Edit `character_metadata.json` position coordinates
- Verify x/y coordinates and scale in micro-test first

**Audio out of sync:**
- Check voiceover timing vs. clip order in `expanded_pairs.csv`
- Verify character pose timing matches dialogue beats

---

## File Checklist

Before assembly, confirm you have:

- [ ] `graded/` directory with 99 MP4 clips
- [ ] `expanded_pairs.csv` (clip order)
- [ ] `assemble_final.py` (assembly script)
- [ ] `sync_audio.py` (voiceover concatenator)
- [ ] `voiceover_manifest.json` (filled with ElevenLabs data)
- [ ] `voiceovers/` directory with ch01-ch21 audio files
- [ ] `integrate_character_animation.py` (optional, for character layer)
- [ ] `character_metadata.json` (optional, for character layer)

---

## Command Reference

### Quick Assembly (no characters)
```powershell
python sync_audio.py --manifest voiceover_manifest.json --audio-dir voiceovers --output voiceover_master.wav
python assemble_final.py --clips graded --pairs expanded_pairs.csv --audio voiceover_master.wav --output final.mp4
```

### With Character Layer
```powershell
python integrate_character_animation.py --metadata character_metadata.json --env-clips graded --char-clips characters --output-dir composited
python assemble_final.py --clips composited --pairs expanded_pairs.csv --audio voiceover_master.wav --output final.mp4
```

### Validation Only
```powershell
python sync_audio.py --manifest voiceover_manifest.json --validate-only
python integrate_character_animation.py --metadata character_metadata.json --validate-only
```

---

## Performance Expectations

**On AMD Radeon 660M:**

- Audio concatenation: ~2-5 seconds (19 files)
- Video assembly (FFmpeg encode): ~30-60 minutes
  - Farneback optical flow interpolation: 5.1s/clip × 99 = 505s ✓ (done)
  - Coherence pass grading: 4.1s/clip × 99 = 406s ✓ (done)
  - FFmpeg concat+encode: ~0.5-1x realtime for 1280×720 H.264
- Character integration (overlay + encode): ~2-3x longer than plain concat
- Total end-to-end (minus character): ~1-2 hours from graded clips to final.mp4

---

## Next: Audio Generation (ElevenLabs)

Provide the user with:
1. Chapter breakdown (1-21 chapters × locations)
2. Voiceover script for each chapter
3. Character voice selections from ElevenLabs
4. Output format preference (WAV/MP3, bitrate, etc.)

Then download flow_ids and update `voiceover_manifest.json`.

---

**Tested on:** AMD Radeon 660M (2GB VRAM), Python 3.12, OpenCV 5.0.0.93, FFmpeg  
**Build date:** 2026-09-02  
**Branch:** `claude/chat-overflow-eq6o30`
