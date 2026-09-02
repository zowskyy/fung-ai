# NO SAND BEACH -- Sprite Sheet Specification

**Generated** by `tools/sprite_pipeline.py spec` from the animation shot list.
Do not hand-edit. This is the contract the Blender render must match exactly --
Godot reads frame regions from these coordinates, so a row rendered out of order
produces silently wrong animation rather than an error.

**13 sheets, 56 clips, 292 frames total.**

## Layout rules

- One sheet per character. Cell size **512x768** px, transparent background.
- **One row per clip**, in the order listed below (alphabetical by clip name).
- Frames run **left to right** within a row, starting at column 0.
- Rows are padded to the sheet's full width. A clip with fewer frames than the
  widest clip leaves its trailing cells **empty** -- do not pack them.
- Render at **12.0fps** playback intent, black and white, matching
  `RENDER_STYLE.md`. The CA-dissolve pass runs later, on the composited frame.

## Classmate A (generic extra)

`classmate_a` — **1 clips**, sheet **3072x768** px (6 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/classmate_a/classmate_a_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`talk`** | 6 | yes | in_place | 1 |

## Classmate B (generic extra)

`classmate_b` — **1 clips**, sheet **3072x768** px (6 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/classmate_b/classmate_b_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`talk`** | 6 | yes | in_place | 1 |

## Delia

`delia` — **10 clips**, sheet **4096x7680** px (8 columns x 10 rows)

Save to `res://NO_SAND_BEACH/assets/characters/delia/delia_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`change_clothes`** | 4 | **no** (holds last frame) | none | 1 |
| 1 | **`hand_on_hand`** | 4 | **no** (holds last frame) | none | 1 |
| 2 | **`kiss_forehead`** | 4 | **no** (holds last frame) | none | 1 |
| 3 | **`look_out`** | 6 | yes | in_place | 1 |
| 4 | **`pour_coffee`** | 4 | **no** (holds last frame) | none | 1 |
| 5 | **`sit_idle`** | 6 | yes | in_place | 1 |
| 6 | **`stand_up`** | 4 | **no** (holds last frame) | none | 1 |
| 7 | **`talk`** | 6 | yes | in_place | 8 |
| 8 | **`walk`** | 8 | yes | planar_root_motion | 2 |
| 9 | **`watch`** | 6 | yes | in_place | 1 |

## Earl (memory design, period-styled)

`earl` — **3 clips**, sheet **3072x2304** px (6 columns x 3 rows)

Save to `res://NO_SAND_BEACH/assets/characters/earl/earl_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`hold_child`** | 4 | **no** (holds last frame) | none | 1 |
| 1 | **`talk`** | 6 | yes | in_place | 1 |
| 2 | **`vanish`** | 4 | **no** (holds last frame) | none | 1 |

## Earl (glitch design -- CA-choppy thread mask)

`earl_glitch` — **2 clips**, sheet **3072x1536** px (6 columns x 2 rows)

Save to `res://NO_SAND_BEACH/assets/characters/earl_glitch/earl_glitch_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`glitch_in`** | 4 | **no** (holds last frame) | none | 1 |
| 1 | **`talk`** | 6 | yes | in_place | 2 |

## Interviewer (generic, modular across the montage)

`interviewer` — **1 clips**, sheet **3072x768** px (6 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/interviewer/interviewer_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`talk`** | 6 | yes | in_place | 2 |

## Judge (generic; shares Seq 5's design)

`judge` — **3 clips**, sheet **3072x2304** px (6 columns x 3 rows)

Save to `res://NO_SAND_BEACH/assets/characters/judge/judge_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`gavel`** | 4 | **no** (holds last frame) | none | 2 |
| 1 | **`preside`** | 6 | yes | in_place | 1 |
| 2 | **`talk`** | 6 | yes | in_place | 2 |

## Marcus

`marcus` — **7 clips**, sheet **4096x5376** px (8 columns x 7 rows)

Save to `res://NO_SAND_BEACH/assets/characters/marcus/marcus_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`embrace`** | 4 | **no** (holds last frame) | none | 1 |
| 1 | **`look_out`** | 6 | yes | in_place | 1 |
| 2 | **`set_down`** | 4 | **no** (holds last frame) | none | 1 |
| 3 | **`sit_idle`** | 6 | yes | in_place | 1 |
| 4 | **`stand_up`** | 4 | **no** (holds last frame) | none | 1 |
| 5 | **`talk`** | 6 | yes | in_place | 9 |
| 6 | **`walk`** | 8 | yes | planar_root_motion | 4 |

## Arresting Officer (generic extra)

`officer` — **1 clips**, sheet **3072x768** px (6 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/officer/officer_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`talk`** | 6 | yes | in_place | 2 |

## Pure (age 15 design)

`pure` — **24 clips**, sheet **4096x18432** px (8 columns x 24 rows)

Save to `res://NO_SAND_BEACH/assets/characters/pure/pure_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`close_laptop`** | 4 | **no** (holds last frame) | none | 3 |
| 1 | **`collapse`** | 4 | **no** (holds last frame) | none | 1 |
| 2 | **`cuffed`** | 4 | **no** (holds last frame) | none | 1 |
| 3 | **`deflate`** | 4 | **no** (holds last frame) | none | 1 |
| 4 | **`eat`** | 6 | yes | in_place | 1 |
| 5 | **`kneel`** | 4 | **no** (holds last frame) | none | 1 |
| 6 | **`lie_idle`** | 6 | yes | in_place | 1 |
| 7 | **`listen`** | 6 | yes | in_place | 1 |
| 8 | **`look_out`** | 6 | yes | in_place | 2 |
| 9 | **`read`** | 6 | yes | in_place | 1 |
| 10 | **`recoil`** | 4 | **no** (holds last frame) | none | 1 |
| 11 | **`sit_idle`** | 6 | yes | in_place | 6 |
| 12 | **`sit_up`** | 4 | **no** (holds last frame) | none | 1 |
| 13 | **`sleep`** | 6 | yes | in_place | 1 |
| 14 | **`smile`** | 4 | **no** (holds last frame) | none | 1 |
| 15 | **`stand_idle`** | 6 | yes | in_place | 2 |
| 16 | **`stand_up`** | 4 | **no** (holds last frame) | none | 2 |
| 17 | **`talk`** | 6 | yes | in_place | 14 |
| 18 | **`teach`** | 8 | yes | planar_root_motion | 1 |
| 19 | **`touch_sand`** | 4 | **no** (holds last frame) | none | 1 |
| 20 | **`turn_to_look`** | 4 | **no** (holds last frame) | none | 1 |
| 21 | **`type`** | 6 | yes | in_place | 3 |
| 22 | **`wake`** | 4 | **no** (holds last frame) | none | 1 |
| 23 | **`walk`** | 8 | yes | planar_root_motion | 5 |

## Pure (age 7 design, flashback only)

`pure_child` — **1 clips**, sheet **2048x768** px (4 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/pure_child/pure_child_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`held`** | 4 | **no** (holds last frame) | none | 1 |

## Pure (age 15 design, arrest beat only)

`pure_teen` — **1 clips**, sheet **2048x768** px (4 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/pure_teen/pure_teen_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`cuffed`** | 4 | **no** (holds last frame) | none | 1 |

## Student (generic extra)

`student_kid` — **1 clips**, sheet **3072x768** px (6 columns x 1 rows)

Save to `res://NO_SAND_BEACH/assets/characters/student_kid/student_kid_sheet.png`

| Row | Clip | Frames | Loop | Motion | Beats |
|---|---|---|---|---|---|
| 0 | **`talk`** | 6 | yes | in_place | 1 |
