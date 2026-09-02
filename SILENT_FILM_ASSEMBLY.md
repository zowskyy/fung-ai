# Silent Film Assembly — No Sand Beach

**Approach:** Expressionist character animation + text subtitles (no audio)  
**Format:** MP4 video with embedded subtitle rendering (or separate .srt file)  
**Character performance:** Pose changes and gestures create dialogue illusion  
**Final output:** Silent film ready for Godot VideoPlayer

---

## Assembly Pipeline (Simplified)

```
99 graded clips (environment)
        ↓
integrate_character_animation.py
        ↓
99 composited clips (environment + character animation)
        ↓
generate_subtitles.py
        ↓
subtitle file (SRT/VTT/JSON)
        ↓
assemble_silent_film.py (FFmpeg concat + subtitle overlay)
        ↓
final_silent.mp4 (no audio, subtitles burned in)
        ↓
Godot VideoPlayer import
```

---

## Step 1: Generate Character Metadata (Story-Based)

Create `character_metadata_silent.json` mapping story breakdown to character poses:

```json
{
  "metadata": {
    "format": "silent_film_with_subtitles",
    "chapters": 21,
    "total_duration": "8.61 seconds",
    "subtitle_file": "subtitles.srt"
  },
  "scenes": [
    {
      "clip_id": "beach_01",
      "chapter": 1,
      "location": "beach",
      "character_id": "protagonist",
      "image": "pureteen.png",
      "position": {"x": 640, "y": 540, "scale": 1.0},
      "pose": "standing_looking_distant",
      "emotion": "nostalgic",
      "subtitle_sync": {
        "start": 0.0,
        "end": 0.41,
        "text": "Ten miles from the ocean.\nNever touched the sand."
      }
    },
    {
      "clip_id": "beach_02",
      "chapter": 2,
      "location": "beach",
      "character_id": "mother",
      "image": "mama.png",
      "position": {"x": 640, "y": 540, "scale": 1.0},
      "pose": "working_exhausted",
      "emotion": "sacrifice",
      "subtitle_sync": {
        "start": 0.41,
        "end": 0.82,
        "text": "Mom worked three jobs.\nShe never complained."
      }
    }
    // ... continue for all 99 scenes
  ]
}
```

---

## Step 2: Generate Subtitles

```bash
python generate_subtitles.py --format srt --output subtitles.srt
# OR
python generate_subtitles.py --format json --output subtitles_godot.json
```

**Output:**
```
1
00:00:00,000 --> 00:00:00,410
Ten miles from the ocean.
Never touched the sand.

2
00:00:00,410 --> 00:00:00,820
Mom worked three jobs.
She never complained.

...
```

---

## Step 3: Integrate Character Animation

```bash
python integrate_character_animation.py \
  --metadata character_metadata_silent.json \
  --env-clips graded \
  --char-clips characters \
  --output-dir composited_silent
```

**Output:** 99 MP4 files with characters overlaid on environment clips

---

## Step 4: Assemble Silent Film (Video Only, No Audio)

Create `assemble_silent_film.py`:

```bash
python assemble_silent_film.py \
  --clips composited_silent \
  --pairs expanded_pairs.csv \
  --subtitles subtitles.srt \
  --output final_silent.mp4
```

This script:
1. Concatenates all 99 clips with crossfades at location boundaries
2. Burns subtitle overlay directly into video (or uses FFmpeg subtitle filter)
3. No audio muxing (skip sync_audio.py entirely)
4. Output: final_silent.mp4 (~8.6 seconds, 1280×720 H.264)

---

## FFmpeg Command for Silent Film Assembly

```bash
# Simple concat (no subtitles)
ffmpeg \
  -i composited_silent/beach_01.mp4 \
  -i composited_silent/beach_02.mp4 \
  -i composited_silent/beach_03.mp4 \
  ... (99 clips) \
  -filter_complex "[0:v][1:v]...[98:v]concat=n=99:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 -preset medium -crf 18 \
  final_silent.mp4

# With subtitles burned in
ffmpeg \
  -i concat_video.mp4 \
  -vf "subtitles=subtitles.srt" \
  -c:v libx264 -preset medium -crf 18 \
  final_silent_with_subtitles.mp4
```

---

## Alternative: Subtitles in Godot (More Flexible)

Instead of burning subtitles into video, you can:

1. Export `final_silent.mp4` (video only)
2. Export `subtitles_godot.json` (timing + text)
3. In Godot, render subtitles as UI overlay synchronized with VideoPlayer

**Advantage:** Can adjust font, size, position, styling without re-encoding video  
**Process:**
```gdscript
# In Godot VideoPlayer scene
extends Control

@onready var video_player = $VideoPlayer
@onready var subtitle_label = $SubtitleLabel

var subtitles = []
var current_sub_index = 0

func _ready():
    var subtitle_file = load("res://assets/subtitles_godot.json")
    subtitles = subtitle_file["subtitles"]
    video_player.play()

func _process(_delta):
    var current_time = video_player.stream.get_length() * video_player.get_stream_playback_position()
    
    # Find matching subtitle
    for sub in subtitles:
        if sub["start"] <= current_time <= sub["end"]:
            subtitle_label.text = sub["text"]
            return
    
    subtitle_label.text = ""
```

---

## Character Performance Strategy

Since this is a **silent film**, character animation must communicate dialogue through gesture:

### Pose Mapping for Dialogue Simulation

| Emotion/State | Character Image | Action | Scene |
|---|---|---|---|
| Nostalgic reflection | pureteen.png | Standing, looking away | Beach opening |
| Exhaustion/sacrifice | mama.png | Bent, working posture | Kitchen scenes |
| Grief | pure.png | Close-up face, eyes down | Father death (Chapter 4) |
| Determination | pure.png | Intense focus, forward gaze | Prison (Chapter 9) |
| Seduction/pride | pureyoung1.png | Confident, head up | App success (Chapter 15) |
| Horror/dissolution | pure.png | Fragmented, distorted | Glitch chapter (Chapter 16-18) |
| Reconciliation | purebrother5.png | Embrace gesture, open body | Hospital (Chapter 19) |
| Wisdom/peace | pureolder1.png | Grounded, balanced stance | Beach finale (Chapter 21) |

### Pose Transitions Within Scenes

Alternate character images within the same clip to show subtle movement:

- **Chapters 1-3:** pureteen standing → mama working → brother watching
- **Chapters 7-9:** pure focused → pure intense coding → pure exhausted
- **Chapter 19:** mama compassionate → pure vulnerable → purebrother embracing
- **Chapter 21:** whole family together, slow pan through generations

---

## Subtitle Styling (Godot Font Parameters)

**Recommended for silent film:**

```gdscript
var subtitle_font = load("res://fonts/silent_film.tres")

# Settings:
font_size: 32
font_color: Color.WHITE
outline_width: 2
outline_color: Color.BLACK
horizontal_alignment: HORIZONTAL_ALIGNMENT_CENTER
vertical_alignment: VERTICAL_ALIGNMENT_BOTTOM
```

**Why:** White text with black outline reads clearly over any environment background (film noir tradition)

---

## Timeline Breakdown

| Phase | Time | Command |
|-------|------|---------|
| Character metadata prep | 30 min | Manual creation of character_metadata_silent.json |
| Character integration | 20-30 min | `integrate_character_animation.py` (99 clips) |
| Subtitle generation | <1 min | `generate_subtitles.py` |
| Silent film assembly | 5-10 min | FFmpeg concat + subtitle overlay |
| QA in Godot | 15 min | Test VideoPlayer timing and subtitle sync |
| **Total** | ~1.5 hours | From graded clips to final_silent.mp4 |

---

## Quality Assurance Checklist

- [ ] All 99 clips in composited_silent/ (verify count)
- [ ] Subtitles.srt has 21 entries with correct timing
- [ ] Character images display clearly over environment backgrounds
- [ ] Subtitle text is readable (white on black outline)
- [ ] Clip order follows story narrative
- [ ] Crossfades at location boundaries are smooth
- [ ] Total video duration ~8.6 seconds
- [ ] Video plays in media player without artifacts
- [ ] Godot VideoPlayer plays final_silent.mp4 without errors
- [ ] Subtitle timing syncs with video playback
- [ ] Character poses match emotional beats of subtitle text

---

## Godot Integration (Final Step)

### In Godot Editor

1. **Create VideoPlayer scene:**
```gdscript
extends Control
class_name SilentFilmPlayer

@onready var video_player = $VideoPlayer
@onready var subtitle_label = $SubtitleLabel

func _ready():
    var video_stream = load("res://assets/video/final_silent.mp4")
    video_player.set_stream(video_stream)
    video_player.play()
```

2. **Load subtitles (if separate from video):**
```gdscript
func load_subtitles(json_path: String):
    var file = FileAccess.open(json_path, FileAccess.READ)
    var json = JSON.parse_string(file.get_as_text())
    return json["subtitles"]
```

3. **Synchronize subtitle display:**
```gdscript
func _process(_delta):
    if video_player.stream and video_player.is_playing():
        var current_time = video_player.stream.get_length() * video_player.get_stream_playback_position()
        
        for sub in subtitles:
            if sub["start"] <= current_time <= sub["end"]:
                subtitle_label.text = sub["text"]
                return
        
        subtitle_label.text = ""
```

---

## Files Generated

```
/ (root)
├── character_metadata_silent.json      # Story-mapped character poses
├── subtitles.srt                       # 21 chapters, timing-accurate
├── subtitles_godot.json                # Same, JSON format for Godot
│
├── composited_silent/
│   ├── beach_01.mp4 through beach_05.mp4
│   ├── car_01.mp4 through car_05.mp4
│   ├── ... (99 total)
│   └── schoolyard_01.mp4 through schoolyard_05.mp4
│
└── final_silent.mp4                    # Final output (1280×720, 8.6s, no audio)
```

---

## Performance Expectations (660M)

| Step | Time |
|------|------|
| Character integration (99 clips) | 15-30 min |
| Subtitle generation | <1 min |
| FFmpeg concat+subtitle burn | 5-10 min |
| **Total** | ~1 hour |

---

## Why This Works for Silent Film

1. **No audio sync complexity** — pure visual + text storytelling
2. **Character animation as dialogue** — expressionist poses communicate emotion
3. **Subtitles ground the narrative** — text clarifies abstract visual poetry
4. **Silent film tradition** — audiences understand wordless performance + captions
5. **Godot integration** — subtitles can be rendered as UI, allowing live adjustment

---

## Final Output for Godot

```
final_silent.mp4 + subtitles_godot.json
├── Video: Graded B&W expressionist environment + character animation
├── Format: H.264, 1280×720, 24fps, 8.6 seconds, no audio
├── Story: 21 chapters of Pure's journey (setup → fall → redemption)
├── Subtitles: 21 key phrases timed to character poses
└── Ready for: VideoPlayer scene in Godot with subtitle sync
```

---

**Status:** Architecture designed for silent film with subtitles  
**Next:** Customize character_metadata_silent.json with story-specific poses, generate subtitles, run assembly  
**Timeline:** ~1 hour from character integration to final_silent.mp4
