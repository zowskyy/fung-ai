# NO SAND BEACH — Render Style: CA-Dissolved Pixel Focus

**Status:** Design locked, not yet implemented. This is Phase D (Headless Rendering) work — no sprite assets exist yet and no Godot binary is available in this environment, so this document exists to preserve the decision until Phase D actually starts.

This document covers two related but distinct CA-driven visual techniques:
1. **CA-Dissolved Pixel Focus** — the main render style for every sequence (below).
2. **CA-Choppy Glitch** — Earl's Sequence 3 glitch-state appearance, a separate design using the same underlying engine tuned to a different, chaotic (non-convergent) rule instead of the smooth organic-dissolution rule used for the main style. See its own section near the end of this document.

## Concept

Reference: a chunky, hard-edged pixel-art scene (color, Scarface-style gangster interior — the visual density and staging of the reference is the target, not its content or palette).

Adapted for NO SAND BEACH: black-and-white, higher resolution/fidelity than the reference, with faces as the sharp focal point and everything else falling off into soft, organic dissolution — achieved through **cellular automata edge-relaxation**, not a conventional Gaussian depth-of-field blur.

## Why CA instead of blur

This repo's CA engine (`fung_ai_v2/ca_engine.py`) already does exactly this kind of transformation, just for cave geometry instead of rendered frames: `step_ca()` is a standard Moore-neighborhood birth/survival cellular automaton (`CARule`, `B{birth}/S{survival}` — Conway's Game of Life is literally the `B3/S23` special case of this same format), used elsewhere in the project to turn jagged random-noise grids into smooth, organic cave walls over a few iterations. Repurposing that as an image-space filter keeps the film's rendering technique consistent with its procedural-generation identity, rather than reaching for a generic post-process blur.

## Asset sourcing & fidelity budget (added after real generation started)

The "base render" seed images are produced via **ElevenLabs `creative_generate_image`** (model `flux-2-pro` for the first successful tests), not hand-drawn or algorithmically synthesized from geometric primitives — neither the user nor Claude can draw, and this is the path that actually works in this environment (see git history around the Marcus/Delia reference generations for the earlier investigation: local file access to user-pasted reference photos isn't available in this remote environment, and a different AI tool — Hugging Face Spaces — was blocked by a `gradio=none` session setting; ElevenLabs sidesteps both).

**User-directed fidelity split (locked):**
- **Characters get full generation quality.** Detailed prompts, full attention to matching each character's locked `design_reference_notes` (hairstyle, wardrobe, expression, setting). This is where quality investment pays off, since faces are the CA-dissolve technique's sharp focal point.
- **Environments get minimal fidelity investment**, because the CA-dissolve pass is going to push them down toward abstraction anyway. Practical implication: don't spend generation effort or iteration on detailed/polished environment art. Push environment source images down in pixel/detail quality deliberately — as far as possible while still reading as an intentional stylistic choice, not a broken or accidentally blurry render. The CA dissolution pass (background/extremities, *N* ≈ 4–6+ iterations per the pipeline below) is expected to do most of the actual work of making an environment feel "right" for the film; the source art underneath it doesn't need to hold up on its own.
- Practical tuning target: the dissolved environment should sit right at the edge of legibility — "bare," minimal, recognizable as a place but not detailed — one step before it would read as a technical failure (over-blurred, indistinct) rather than a deliberate soft-focus choice.

## Pipeline

1. **Base render** — chunky pixel art, black-and-white palette, hard block edges. This is the "seed" image, deliberately low-fidelity, matching the reference image's blockiness minus color.
2. **Face-focus map** — per frame, per character, mark face region(s) as the sharp-focus target. Everything else (body, background, environment) falls off in focus based on distance from the nearest face region.
3. **CA dissolution pass** — reuse `step_ca()` as an edge-relaxation filter:
   - Threshold the black-and-white render into a binary grid (1 = ink/dark, 0 = paper/light), per region.
   - Run `step_ca()` for *N* iterations, where *N* scales with distance-from-face ("out-of-focus-ness"):
     - Faces: *N* ≈ 0–1 (stays crisp, pixel-art-sharp — this is the focal point).
     - Body/midground: *N* ≈ 2–3 (light smoothing).
     - Background/extremities: *N* ≈ 4–6+ (heavy dissolution into soft, organic shapes — the depth-of-field stand-in).
   - This is the same neighbor-majority smoothing the CA engine already uses for cave walls (`BIOME_RULE`-driven), just applied to rendered pixels instead of terrain cells.
4. **Upscale** — CA-smoothed edges lose 1:1 alignment with the original pixel grid, so the output resolution is higher than the base pixel-art render: supersample the base grid before the CA pass (or run the CA pass at 2–4x scale). This is what delivers "more resolution and fidelity" while keeping the hand-crafted, procedurally-smoothed look instead of a naive photo blur.

## Open items (need Phase D, real sprites, and a Godot/image-processing test pass to resolve)

- **Face-region tagging**: does `character_animator`'s `character_rig.gd` / `character_skeleton.gd` already support tagging a bone/region as "face," or does this need a new marker convention on top of the existing rig system?
- **CA iteration curve**: linear falloff from face distance, or discrete depth bands (face / body / background)? First real visual test (once sprites exist) should tune this rather than guessing further now.
- **Where this runs**: as a Godot shader (real-time, GPU-side CA iteration per frame) vs. an offline Python post-process pass on captured PNG frames (reusing `fung_ai_v2/ca_engine.py` directly, no reimplementation needed). Offline is simpler to build first and matches the project's existing headless-rendering-then-ffmpeg-compile pipeline; a shader version would be a later optimization if per-frame Python processing is too slow across ~4000 frames/sequence.

## Reference

- Reference image: user-supplied concept art (style reference only — composition/blockiness/staging, not content or palette).
- CA technical basis: `fung_ai_v2/ca_engine.py` — `step_ca()`, `CARule` (Moore-neighborhood birth/survival; Conway's Game of Life is the `B3/S23` special case).

---

## Earl's Glitch State (Sequence 3: "The App") — CA-Choppy Thread Mask

**Status:** Design locked, not yet implemented (same Phase D caveat as above).

### Concept

Reference: a dense, scratchy red thread/string-art mask — a face built from tangled linework, hollow eye sockets, hands framing/gripping the face. Haunting, unraveling, decaying quality.

Adapted for NO SAND BEACH: black-and-white, with the thread-density pattern generated procedurally rather than hand-drawn per frame, producing a "choppy" (jagged, discontinuous, glitch-like) texture rather than the smooth organic look of the main render style.

### Scope: full replacement, not a transition effect

When Earl appears as a glitch in Sequence 3, he **is** the thread-mask apparition — this is a distinct "glitch state" design for Earl, separate from and unrelated to his warm, sepia-toned memory appearance in Sequence 1 (Beat 1.14). Earl now effectively has two visual treatments despite being a single age/design character:
- **Memory appearance** (Seq 1): warm, sepia, soft-focus, tender — already specified in `scenes/sequence_01_setup_breakdown.md`.
- **Glitch appearance** (Seq 3): black-and-white, CA-choppy thread mask, hands framing the face — specified here.

No animated transition between the two is needed; each sequence uses its own static/looping design for Earl.

### Technical approach: same engine, different rule

Reuses `step_ca()` from `fung_ai_v2/ca_engine.py`, but tuned to a **chaotic, non-convergent** `CARule` instead of the smooth-convergent organic-blob rules used for cave walls and the main CA-Dissolved Pixel Focus technique above. CA rule-space includes both kinds of behavior: some birth/survival sets settle into smooth organic regions (what the main render style and cave generation use), others stay perpetually chaotic or oscillating, never converging to a stable smooth shape. That chaotic-rule family is the technical basis for "choppy":

1. **Face-mask silhouette** — Earl's face/hands silhouette defines the region the pattern lives inside (the mask shape from the reference image, not a literal photo-realistic face).
2. **Chaotic CA pattern fill** — within that silhouette, run a chaotic-family `CARule` (exact birth/survival set is a Phase D tuning question, not decided here) for a small fixed number of steps — caught mid-chaos rather than iterated to convergence, so the pattern stays fragmented and thread-like instead of smoothing into blobs.
3. **Per-frame reseed or partial reseed** — re-running the chaotic CA step (or partially reseeding it) each frame is what produces the "glitch" quality: the thread pattern visibly shifts/stutters frame to frame instead of holding static, echoing digital corruption rather than hand-animation.
4. **Black and white only** — no grayscale gradient; matches the film's overall palette (the reference image's red is not carried over).

### Open items

- **Exact CARule**: which birth/survival set produces a good chaotic-thread look at the target resolution — needs direct visual iteration once this is actually built, not a guess now.
- **Reseed cadence**: full reseed every frame (maximally chaotic/glitchy) vs. partial reseed every few frames (more readable, less strobe-like) — a legibility question best answered by watching real footage.
- **Hands**: the reference image's hands framing the face are a strong compositional element — confirm whether they're part of the same CA-mask silhouette or a separately-posed (non-CA) element that the CA pattern only fills within.
