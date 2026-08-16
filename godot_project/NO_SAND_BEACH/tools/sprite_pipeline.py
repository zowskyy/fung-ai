"""Sprite sheet contract and Godot clip resources for NO SAND BEACH.

Why this exists
---------------
Between "Blender renders frames" and "Godot plays them" sits a layout contract.
If the Blender side lays a sheet out one way and the Godot side reads it
another, every clip is silently wrong -- offset by a row, or reading a
neighbour's frames -- and the failure shows up as garbled animation rather than
an error. So the layout is written down once, here, and both ends derive from
it: ``spec`` emits the render instruction, ``build`` reads a finished sheet's
spec back into Godot resources.

Why not CharacterAnimationProfile
---------------------------------
``CharacterAnimationProfile`` looks like the obvious target but is the wrong
tool for this film. It models *locomotion* -- ten fixed slots (idle/walk/run/
jump/fall/land/crouch/attack_1/hurt) feeding an ``AnimationTree`` blend space
driven by velocity and grounded-ness. Pure needs 23 clips, most of them one-shot
dramatic poses (``kneel``, ``touch_sand``, ``embrace``, ``collapse``) that no
blend space would ever select, and nothing in the film is driven by velocity.

``CharacterAnimator.clips`` is an arbitrary ``Dictionary`` of named
``AnimationClip`` resources with a direct ``play(name)`` entry point, which is
exactly what a ScenePlan ``ActionBeat`` needs: the beat names an action, the
registry maps it to a clip name, and the animator plays that clip. That is the
whole path -- no state machine, no blend space, no profile.

Frame budget
------------
Frame counts come from the action's ``motion_mode`` rather than being chosen per
clip, so the shot list stays the single source of truth:

- ``in_place``            looping cycles (breathing, typing, talking) -- 6 frames
- ``planar_root_motion``  locomotion that has to read as a full stride -- 8 frames
- ``none``                one-shot poses that play through and hold -- 4 frames

These are deliberately small. The film's CA-dissolve pass (RENDER_STYLE.md)
abstracts everything away from the face, so frame-rate smoothness buys much less
here than it would in a conventionally rendered short. Raise a specific clip's
count in the spec if a beat needs it -- the kneel in 6.02 is the obvious
candidate, being the film's title payoff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Frames per clip, keyed by the action's motion_mode. See the module docstring
# for why these are small.
FRAMES_BY_MOTION: dict[str, int] = {
    "in_place": 6,
    "planar_root_motion": 8,
    "none": 4,
}
DEFAULT_FRAMES = 6

# Clips that must not loop: a one-shot pose plays through and holds its last
# frame. Looping a collapse or an embrace would replay it forever under a held
# camera, which is exactly where this film holds longest.
NON_LOOPING_MOTION = {"none"}

# Playback rate for sprite clips. The film renders at 24fps, but these are
# stylised cycles rather than full-rate animation -- 12 is a deliberate "on
# twos" choice matching the hand-drawn register.
DEFAULT_FPS = 12.0

# Per-frame cell size on the sheet. Portrait, since every clip is a standing or
# kneeling human figure. Revisit once the first real Blender render exists --
# this is a starting contract, not a measured one.
DEFAULT_FRAME_SIZE = (512, 768)

ADDON_RUNTIME = "res://addons/character_animator/runtime"


class SpriteSpecError(Exception):
    """Raised when a sheet specification cannot be built or read."""


def build_sheet_spec(
    shotlist: dict,
    *,
    frame_size: tuple[int, int] = DEFAULT_FRAME_SIZE,
    fps: float = DEFAULT_FPS,
) -> dict[str, Any]:
    """Turn the animation shot list into a per-character sheet layout.

    Each character gets one sheet: one row per clip, frames left to right,
    clips in sorted order so the layout is stable across regenerations. A row
    is as wide as the widest clip; short rows leave trailing cells empty rather
    than packing, because packing would make every row's origin depend on every
    previous row's length -- one clip's frame count changing would silently
    move every clip after it.
    """
    characters: dict[str, Any] = {}

    for actor_id, entry in shotlist["characters"].items():
        clips: list[dict[str, Any]] = []
        for row, (clip_name, clip) in enumerate(sorted(entry["clips"].items())):
            motion = clip.get("motion_mode", "in_place")
            frames = FRAMES_BY_MOTION.get(motion, DEFAULT_FRAMES)
            clips.append({
                "clip": clip_name,
                "row": row,
                "frames": frames,
                "fps": fps,
                "loop": motion not in NON_LOOPING_MOTION,
                "motion_mode": motion,
                "beats": len(clip["beats"]),
            })

        if not clips:
            continue

        columns = max(c["frames"] for c in clips)
        characters[actor_id] = {
            "actor_id": actor_id,
            "display_name": entry["display_name"],
            "sheet_path": f"res://NO_SAND_BEACH/assets/characters/{actor_id}/{actor_id}_sheet.png",
            "frame_size": list(frame_size),
            "columns": columns,
            "rows": len(clips),
            "sheet_size": [frame_size[0] * columns, frame_size[1] * len(clips)],
            "clips": clips,
        }

    return {
        "frame_size": list(frame_size),
        "fps": fps,
        "characters": characters,
        "totals": {
            "characters": len(characters),
            "clips": sum(len(c["clips"]) for c in characters.values()),
            "frames": sum(f["frames"] for c in characters.values() for f in c["clips"]),
        },
    }


def render_spec_markdown(spec: dict) -> str:
    """Render the sheet spec as the instruction the Blender side works from."""
    totals = spec["totals"]
    fw, fh = spec["frame_size"]
    out: list[str] = [
        "# NO SAND BEACH -- Sprite Sheet Specification",
        "",
        "**Generated** by `tools/sprite_pipeline.py spec` from the animation shot list.",
        "Do not hand-edit. This is the contract the Blender render must match exactly --",
        "Godot reads frame regions from these coordinates, so a row rendered out of order",
        "produces silently wrong animation rather than an error.",
        "",
        f"**{totals['characters']} sheets, {totals['clips']} clips, "
        f"{totals['frames']} frames total.**",
        "",
        "## Layout rules",
        "",
        f"- One sheet per character. Cell size **{fw}x{fh}** px, transparent background.",
        "- **One row per clip**, in the order listed below (alphabetical by clip name).",
        "- Frames run **left to right** within a row, starting at column 0.",
        "- Rows are padded to the sheet's full width. A clip with fewer frames than the",
        "  widest clip leaves its trailing cells **empty** -- do not pack them.",
        f"- Render at **{spec['fps']}fps** playback intent, black and white, matching",
        "  `RENDER_STYLE.md`. The CA-dissolve pass runs later, on the composited frame.",
        "",
    ]

    for char in spec["characters"].values():
        sw, sh = char["sheet_size"]
        out.append(f"## {char['display_name']}")
        out.append("")
        out.append(
            f"`{char['actor_id']}` — **{char['rows']} clips**, "
            f"sheet **{sw}x{sh}** px ({char['columns']} columns x {char['rows']} rows)"
        )
        out.append("")
        out.append(f"Save to `{char['sheet_path']}`")
        out.append("")
        out.append("| Row | Clip | Frames | Loop | Motion | Beats |")
        out.append("|---|---|---|---|---|---|")
        for clip in char["clips"]:
            loop = "yes" if clip["loop"] else "**no** (holds last frame)"
            out.append(
                f"| {clip['row']} | **`{clip['clip']}`** | {clip['frames']} | {loop} "
                f"| {clip['motion_mode']} | {clip['beats']} |"
            )
        out.append("")

    return "\n".join(out)


def _quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def pick_initial_animation(clips: list[dict]) -> str:
    """Choose the clip a character rests in before any beat drives them.

    A looping in-place cycle is the only safe default: a one-shot pose would
    play once and hold a dramatic frame (a collapse, an embrace) as the
    character's neutral state. Falls back to the first clip when a character
    has nothing looping -- true of extras whose only clip is a single pose.
    """
    for candidate in ("stand_idle", "sit_idle", "idle", "listen", "talk"):
        for clip in clips:
            if clip["clip"] == candidate and clip["loop"]:
                return candidate
    for clip in clips:
        if clip["loop"]:
            return clip["clip"]
    return clips[0]["clip"]


def build_character_scene(character: dict) -> str:
    """Emit the Godot scene for one character: a CharacterAnimator with its clips.

    ``CharacterAnimator`` extends ``Sprite2D``, so it is a node rather than a
    resource -- its ``clips`` Dictionary lives in a ``.tscn``, not a ``.tres``.
    That also makes the character directly instantiable, which is what a
    ScenePlan's ``SceneActorBinding.actor_path`` needs to point at.

    Frame regions are computed from the row/column layout, which is why the
    rendered sheet has to match the spec exactly -- a row rendered out of order
    reads a neighbour's frames with no error to catch it.
    """
    fw, fh = character["frame_size"]
    clips = character["clips"]
    if not clips:
        raise SpriteSpecError(f"{character['actor_id']} has no clips.")

    ext = [
        f'[ext_resource type="Script" '
        f'path="{ADDON_RUNTIME}/character_animator.gd" id="1_animator"]',
        f'[ext_resource type="Script" path="{ADDON_RUNTIME}/animation_clip.gd" id="2_clip"]',
        f'[ext_resource type="Texture2D" path="{character["sheet_path"]}" id="3_sheet"]',
    ]

    subs: list[str] = []
    entries: list[str] = []
    for clip in clips:
        sub_id = f"Resource_clip_{clip['clip']}"
        regions = ", ".join(
            f"Rect2({col * fw}, {clip['row'] * fh}, {fw}, {fh})" for col in range(clip["frames"])
        )
        subs.append(
            "\n".join([
                f'[sub_resource type="Resource" id="{sub_id}"]',
                'script = ExtResource("2_clip")',
                f'name = &{_quote(clip["clip"])}',
                f"frames = Array[Rect2]([{regions}])",
                f"fps = {float(clip['fps'])}",
                f"loop = {'true' if clip['loop'] else 'false'}",
            ])
        )
        entries.append(f'&{_quote(clip["clip"])}: SubResource("{sub_id}")')

    node_name = "".join(part.capitalize() for part in character["actor_id"].split("_"))
    load_steps = len(ext) + len(subs)
    return (
        "\n".join([
            f'[gd_scene load_steps={load_steps} format=3]',
            "",
            "\n".join(ext),
            "",
            "\n\n".join(subs),
            "",
            f'[node name="{node_name}" type="Sprite2D"]',
            'script = ExtResource("1_animator")',
            'texture = ExtResource("3_sheet")',
            "clips = {",
            ",\n".join(entries),
            "}",
            f'initial_animation = &{_quote(pick_initial_animation(clips))}',
            "auto_play = true",
        ])
        + "\n"
    )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_spec = sub.add_parser("spec", help="Generate the sheet spec from the shot list.")
    p_spec.add_argument("shotlist", type=Path)
    p_spec.add_argument("--json", dest="json_out", type=Path, default=None)
    p_spec.add_argument("--markdown", type=Path, default=None)
    p_spec.add_argument("--frame-width", type=int, default=DEFAULT_FRAME_SIZE[0])
    p_spec.add_argument("--frame-height", type=int, default=DEFAULT_FRAME_SIZE[1])
    p_spec.add_argument("--fps", type=float, default=DEFAULT_FPS)

    p_build = sub.add_parser("build", help="Emit the character scene (.tscn) for one actor.")
    p_build.add_argument("spec", type=Path)
    p_build.add_argument("actor_id")
    p_build.add_argument("output", type=Path)

    args = parser.parse_args(argv)

    if args.command == "spec":
        spec = build_sheet_spec(
            _load(args.shotlist),
            frame_size=(args.frame_width, args.frame_height),
            fps=args.fps,
        )
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {args.json_out}")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_spec_markdown(spec), encoding="utf-8")
            print(f"wrote {args.markdown}")
        t = spec["totals"]
        print(f"{t['characters']} sheets, {t['clips']} clips, {t['frames']} frames")
        return 0

    spec = _load(args.spec)
    character = spec["characters"].get(args.actor_id)
    if character is None:
        known = ", ".join(sorted(spec["characters"]))
        print(f"No character '{args.actor_id}' in spec. Known: {known}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_character_scene(character), encoding="utf-8")
    print(f"wrote {args.output} ({len(character['clips'])} clips)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
