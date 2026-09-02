# Character Asset Inventory — No Sand Beach Animation

**Date:** 2026-09-02  
**Status:** Assets extracted and cataloged from ElevenLabs generation  
**Location:** `characters/` directory  
**Total files:** 20 character/scene assets

---

## Character Family Overview

The "Pure" family consists of multiple generations and perspectives on the same narrative.

### Character Archetypes

| Character | Files | Role | Age | Visual | Scenes |
|-----------|-------|------|-----|--------|--------|
| **Pure** | pure.png | Protagonist (intimate POV) | Teen/Young Adult | Close-up face, expressive eye | Reflective moments |
| **Pureteen** | pureteen.png, pureteen1-4.png | Protagonist (full body) | Teen (14-16) | Casual wear, full figure | Active, contemporary |
| **Pureyoung** | pureyoung1-2.png | Protagonist (young) | Young Adult (20s) | Various poses | Narrative transitions |
| **Pureolder** | pureolder1-2.png | Protagonist (aged) | Adult (30s+) | Matured version | Reflection, wisdom |
| **Purebrother** | purebrother.png, purebrother2-6.png | Brother character | Various ages | Multiple states/emotions | Family dynamics |
| **Delia** | delia.png | Supporting character | Young Adult | Distinct design | Specific scenes |
| **Mama** | mama.png | Mother | Adult | Home setting, dramatic lighting | Kitchen/domestic |
| **Puredadglitch** | puredadglitch.jpg | Father | Adult | Glitch effect overlay | Fragmented memories |
| **Purehousestreet** | purehousestreet.png | Scene/environment | N/A | Interior architecture | Location shots |

---

## Asset Files Detailed

### Protagonist Variations

**pure.png** (506 KB)
- Close-up, intimate composition
- Large expressive eye with iris detail
- Face partially obscured/framed
- Film noir aesthetic
- Perfect for: voiceover moments, emotional beats, internal reflection
- Scale: ~60% of frame width at center position

**pureteen.png** (?)
- Full-body standing pose
- Casual t-shirt and jeans
- Neutral/serious expression
- Contemporary teenage aesthetic
- Perfect for: active scenes, location transitions, dialogue
- Scale: ~40-50% of frame width

**pureteen1.png** through **pureteen4.png**
- Teen character pose variations
- Different emotional states and angles
- Multiple action poses
- Perfect for: sequence animation, pose-to-pose transitions
- Recommended use: cycle through for natural movement

**pureyoung1.png**, **pureyoung2.png** (pureyoung3.jpg also available)
- Young adult character state
- Narrative progression from teen
- Emotional maturity progression
- Perfect for: time passage sequences, internal growth arcs

**pureolder1.png**, **pureolder2.png**
- Aged character version
- Wisdom/reflection aesthetic
- Thematic closure
- Perfect for: finale sequences, reflection moments

### Supporting Characters

**purebrother.png** through **purebrother6.png** (6 variations)
- Family dynamic character
- Multiple emotional/physical states
- Age progression possible
- Perfect for: relationship scenes, family moments, dialogue exchanges

**delia.png** (363 KB)
- Distinct secondary character
- Different design language but compatible style
- Supporting role
- Perfect for: scenes featuring this character specifically

**mama.png** (3.0 MB)
- Domestic/kitchen setting integration
- Adult character authority
- Atmospheric composition
- Perfect for: family scenes, kitchen moments, authority/guidance scenes

**puredadglitch.jpg** (3.5 MB)
- Father character with visual effect
- Glitch overlay suggests memory/fragmentation
- Symbolic/thematic weight
- Perfect for: emotional climax, memory sequences, broken moments

**purehousestreet.png** (3.6 MB)
- Full scene/environment
- Interior architecture
- Atmospheric lighting
- Perfect for: establishing shots, scene context

---

## Scene Integration Strategy

### By Chapter/Location

#### Beach Chapter (Clips beach_01-05)
- **Primary character:** pureteen (full-body beach scenes)
- **Alternate:** pure (introspective moments)
- **Position:** Center-bottom of frame, scale 1.0
- **Poses:** standing, walking, sitting on sand
- **Transitions:** fade-in at scene start, fade-out at transition

#### Car Chapter (Clips car_01-05)
- **Primary character:** pureteen (confined interior)
- **Support:** purebrother variants (passenger/driver perspectives)
- **Position:** Right side of frame (driver), left side (passenger)
- **Poses:** sitting (driving), turning, reaching
- **Transitions:** quick cuts for dialogue, synchronized with audio

#### Forest Chapter (Clips forest_01-05)
- **Primary character:** pure or pureyoung (introspective, outdoor)
- **Position:** Left or center, depending on composition balance
- **Poses:** walking, stopping, looking around
- **Transitions:** dissolve between poses for natural movement

#### Kitchen Chapter (Clips kitchen_01-05)
- **Primary character:** mama (authority/nurturing)
- **Support:** pureteen (childhood/family dynamic)
- **Position:** Mama center (door/counter), teen right or left
- **Poses:** mama standing, teen approaching/seated
- **Transitions:** synchronized with voiceover rhythm

#### Park Chapter (Clips park_01-05)
- **Primary character:** pureteen or pureyoung (contemplative outdoor)
- **Position:** Center or left, with environment space visible
- **Poses:** sitting, standing, looking into distance
- **Transitions:** slow fade for meditative moments

#### Schoolyard Chapter (Clips schoolyard_01-05)
- **Primary character:** pureteen (youth, memory)
- **Support:** purebrother (peer relationship)
- **Position:** Center or right, with schoolyard environment space
- **Poses:** standing together, movement, gesture
- **Transitions:** crossfade for dialogue exchanges

---

## Pose Library for Animation

### Actionable Pose Categories

**Repose (Standing variants)**
- pureteen.png — neutral standing
- pureteen1-4.png — standing variations
- pure.png — close-up emotional states

**Movement Sequences**
- purebrother variants (1-6) — suggest walking/action progression
- pureyoung variants — age progression as movement

**Emotional States**
- pure.png — vulnerability, introspection
- pureteen variants — determination, confusion, acceptance
- mama.png — presence, authority
- puredadglitch.jpg — fragmentation, loss

**Compositional Variants**
- Full-body (pureteen, purebrother, pureyoung, pureolder)
- Close-up (pure, delia)
- Scene-integrated (mama, purehousestreet)

---

## Next Steps: Animation Planning

### 1. Scene-by-Scene Character Placement

For each clip (beach_01 through schoolyard_99):
- [ ] Assign primary character (which PNG file?)
- [ ] Define position (x, y, scale)
- [ ] Define timing (when does character appear/disappear?)
- [ ] Define pose transitions (which files in sequence?)

### 2. Voiceover Sync

Map each character line to:
- [ ] Scene/clip timing
- [ ] Character pose that matches dialogue emotion
- [ ] Mouth position (if doing lip-sync)
- [ ] Gesture/body language that reinforces audio

### 3. Micro-Test Setup

Create single composite for validation:
- [ ] Pick one beach clip (beach_01)
- [ ] Choose character (pureteen.png)
- [ ] Position at center-bottom (x: 640, y: 540, scale: 1.0)
- [ ] Run integrate_character_animation.py micro-test
- [ ] Verify character quality and layering

### 4. Full Batch Production

Once micro-test passes:
- [ ] Generate character_metadata.json with all scene placements
- [ ] Run integrate_character_animation.py for full batch
- [ ] Output composited/ directory with all 99 clips
- [ ] Assemble final video with composited clips

---

## Technical Notes

**File Sizes:**
- Small (close-up): 200KB-500KB (pure.png, delia.png)
- Medium (full-body): 400KB-800KB (pureteen, purebrother, pureyoung, pureolder)
- Large (scene): 3-4MB (mama.png, puredadglitch.jpg, purehousestreet.png)

**Resolution Considerations:**
- Characters: Appear to be 1-2K resolution (suitable for 1280×720 overlay)
- Scaling: Base scale 1.0 = original size; 0.5-2.0 adjustable per scene
- Transparency: PNG files may need alpha channel verification for overlay

**Processing Time Estimate:**
- Per-clip overlay (FFmpeg): 5-10 seconds on 660M
- Full batch (99 clips): 8-15 minutes overlay + encode
- Total with audio sync: ~30-45 minutes from composited clips to final.mp4

---

## Recommended Implementation Order

1. **This week:**
   - [ ] Create character_metadata.json template
   - [ ] Define beach_01 scene (test composition)
   - [ ] Run micro-test with pureteen.png
   - [ ] Verify visual quality and sync

2. **Next week:**
   - [ ] Populate character_metadata.json for all 99 scenes
   - [ ] Map voiceover timing to character poses
   - [ ] Run full batch integration
   - [ ] Generate composited/ directory

3. **Final:**
   - [ ] Assemble final.mp4 with characters
   - [ ] QA check: character positioning, pose timing, audio sync
   - [ ] Export for Godot

---

## Visual Style Notes

All character assets maintain:
- **B&W expressionist aesthetic** (matches environment grain+vignette)
- **Sharp, deliberate linework** (clean vectors, high contrast)
- **Emotional intensity** through facial expression and body language
- **Minimalist simplification** (geometric proportions, symbolic detail)
- **Film noir / manga influence** (dramatic lighting, expressive eyes)

These characteristics align perfectly with the graded environment clips—they will composite seamlessly with the histogram-matched, grained, vignetted background footage.

---

## Character Metadata Structure

See `character_metadata.json` template generated by:
```bash
python integrate_character_animation.py --create-template
```

Template will be populated with:
```json
{
  "characters": [
    {
      "name": "protagonist",
      "image": "pureteen.png",
      "scale": 1.0,
      "style": "expressionist B&W, dynamic young adult"
    },
    ...
  ],
  "scenes": [
    {
      "clip_id": "beach_01",
      "character": "protagonist",
      "image": "pureteen.png",
      "position": {"x": 640, "y": 540, "scale": 1.0},
      "timing": {"start": 0.0, "end": 0.41}
    },
    ...
  ]
}
```

---

**Status:** Ready for scene-by-scene animation planning  
**Next action:** Populate character_metadata.json based on voiceover script and scene breakdown
