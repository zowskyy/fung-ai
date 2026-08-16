"""Derive the per-character animation shot list from the beat sheets.

Why this exists
---------------
Phase B (building and animating the characters in Blender) is the film's
critical path, and the expensive way to get it wrong is to animate the wrong
set of clips -- to spend a day on a walk cycle a character never performs, or
to discover at integration time that Pure needs a "kneel" nobody made.

That information is already implied by the beat sheets: every ``action`` beat
names an ``actor_id`` and an ``action_id``, and the capability registry maps
each ``action_id`` to the ``animation_state`` clip that has to exist. Joining
those two gives the exact, complete clip list per character -- derived from the
film rather than guessed at, and re-derived automatically whenever a beat sheet
changes.

The output is deliberately two-headed: a Markdown shot list a person can work
from at the Blender machine, and a JSON manifest the sprite-import tooling
consumes later so the same source of truth drives both.

It also reports clips the registry defines but no sequence uses. Those are dead
weight -- animating them is wasted work -- so they are surfaced rather than
silently carried.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Beat types that put a character on screen performing something. Dialogue
# beats are handled separately: they imply a "talk" clip for the speaker but
# name no action_id, and voice-over speakers are never on screen at all.
ACTION_BEAT_TYPES = ("action", "move_to")

# Actors tagged this way are voice-over only -- they speak but are never
# rendered, so they need no clips at all.
VOICEOVER_TAG = "voiceover"

# The clip a dialogue beat implies for an on-screen speaker.
DIALOGUE_CLIP = "talk"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_shotlist(beatsheets: list[dict], registry: dict) -> dict[str, Any]:
    """Join beat sheets against the registry to get required clips per character.

    Returns a manifest keyed by actor_id. Each character carries the clips they
    perform, and for each clip the actions, sequences, and beats that demand it
    -- so a change to the film traces forward to the animation work, and an
    animator can see why a clip is on the list.
    """
    actions = registry.get("actions", [])
    action_to_clip = {a["id"]: a.get("animation_state", a["id"]) for a in actions}
    motion_mode = {a["id"]: a.get("motion_mode", "none") for a in actions}

    characters: dict[str, dict[str, Any]] = {}
    used_actions: set[str] = set()

    for sheet in beatsheets:
        plan_id = sheet["plan_id"]
        voiceover: set[str] = set()

        for actor in sheet.get("actors", []):
            aid = actor["actor_id"]
            if VOICEOVER_TAG in (actor.get("actor_tags") or []):
                voiceover.add(aid)
                continue
            entry = characters.setdefault(
                aid,
                {
                    "actor_id": aid,
                    "display_name": actor.get("display_name", aid),
                    "actor_tags": actor.get("actor_tags", []),
                    "sequences": [],
                    "clips": {},
                },
            )
            if plan_id not in entry["sequences"]:
                entry["sequences"].append(plan_id)

        for beat in sheet.get("beats", []):
            btype = beat.get("type")

            if btype in ACTION_BEAT_TYPES:
                actor_id = beat.get("actor_id")
                if not actor_id or actor_id in voiceover:
                    continue
                if btype == "move_to":
                    # MoveToBeat has no action_id; its locomotion_mode names the clip.
                    action_id = beat.get("locomotion_mode", "walk")
                    clip = action_id
                else:
                    action_id = beat.get("action_id", "")
                    clip = action_to_clip.get(action_id, action_id)
                    used_actions.add(action_id)

            elif btype == "dialogue":
                actor_id = beat.get("speaker_actor_id")
                if not actor_id or actor_id in voiceover:
                    continue
                action_id = "(dialogue)"
                clip = DIALOGUE_CLIP

            else:
                continue

            entry = characters.get(actor_id)
            if entry is None:
                continue
            clip_entry = entry["clips"].setdefault(
                clip,
                {
                    "clip": clip,
                    "motion_mode": motion_mode.get(action_id, "in_place"),
                    "actions": [],
                    "beats": [],
                },
            )
            if action_id not in clip_entry["actions"]:
                clip_entry["actions"].append(action_id)
            clip_entry["beats"].append({"sequence": plan_id, "beat_id": beat.get("beat_id", "")})

    for entry in characters.values():
        entry["clips"] = dict(sorted(entry["clips"].items()))
        entry["clip_count"] = len(entry["clips"])
        entry["beat_count"] = sum(len(c["beats"]) for c in entry["clips"].values())

    required_clips = {c for e in characters.values() for c in e["clips"]}

    # An action is only genuinely unused when neither its id is referenced by an
    # action beat NOR its clip is required by some other route. Two routes reach
    # a clip without naming an action_id: dialogue beats imply `talk`, and
    # MoveToBeat names its clip through locomotion_mode. Without this second
    # check the report would tell an animator not to build `walk` or `talk` --
    # exactly backwards, since those are the most-used clips in the film.
    unused = sorted(
        a["id"]
        for a in registry.get("actions", [])
        if a["id"] not in used_actions and a.get("animation_state", a["id"]) not in required_clips
    )

    # Characters declared in a plan that never perform anything. Either the
    # actor binding is dead weight, or -- more often -- a beat is missing and
    # someone is standing in frame unanimated.
    silent = sorted(aid for aid, e in characters.items() if e["clip_count"] == 0)

    return {
        "characters": dict(sorted(characters.items())),
        "unused_actions": unused,
        "characters_without_clips": silent,
        "totals": {
            "characters": len(characters),
            "distinct_clips": len(required_clips),
            "clip_assignments": sum(e["clip_count"] for e in characters.values()),
        },
    }


def render_markdown(shotlist: dict) -> str:
    """Render the shot list as a document to work from at the Blender machine."""
    totals = shotlist["totals"]
    out: list[str] = [
        "# NO SAND BEACH -- Animation Shot List",
        "",
        "**Generated** from the beat sheets by `tools/animation_shotlist.py`. Do not hand-edit --",
        "change a beat sheet and regenerate, or the list stops matching the film.",
        "",
        f"{totals['characters']} on-screen characters, "
        f"{totals['distinct_clips']} distinct clip names, "
        f"{totals['clip_assignments']} character-clip pairs to animate.",
        "",
        "`motion_mode` comes from the capability registry: `in_place` clips loop",
        "without moving the character, `planar_root_motion` clips translate them",
        "across the frame, and `none` marks a one-shot pose that plays and holds.",
        "",
    ]

    for entry in shotlist["characters"].values():
        out.append(f"## {entry['display_name']}")
        out.append("")
        out.append(
            f"`{entry['actor_id']}` — appears in {len(entry['sequences'])} sequence(s): "
            f"{', '.join(entry['sequences'])}"
        )
        out.append("")
        out.append(f"**{entry['clip_count']} clips**, driving {entry['beat_count']} beats.")
        out.append("")
        out.append("| Clip | Motion | Used by | Beats |")
        out.append("|---|---|---|---|")
        for clip in entry["clips"].values():
            actions = ", ".join(f"`{a}`" for a in clip["actions"])
            beats = len(clip["beats"])
            out.append(
                f"| **`{clip['clip']}`** | {clip['motion_mode']} | {actions} | {beats} |"
            )
        out.append("")

    if shotlist["characters_without_clips"]:
        out.append("## ⚠ Declared but never animated")
        out.append("")
        out.append("These actors are bound in a plan but perform no action and speak")
        out.append("they would stand in frame unanimated. Usually this means a beat is missing")
        out.append("rather than that the actor should be removed.")
        out.append("")
        for actor_id in shotlist["characters_without_clips"]:
            entry = shotlist["characters"][actor_id]
            seqs = ", ".join(entry["sequences"])
            out.append(f"- `{actor_id}` — {entry['display_name']} ({seqs})")
        out.append("")

    if shotlist["unused_actions"]:
        out.append("## Registered but unused")
        out.append("")
        out.append("These actions exist in the capability registry but no sequence performs them.")
        out.append("Do not animate them unless a beat sheet starts using them.")
        out.append("")
        for action in shotlist["unused_actions"]:
            out.append(f"- `{action}`")
        out.append("")

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--beatsheets", type=Path, required=True, help="Directory of beat sheet JSON."
    )
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, default=None)
    parser.add_argument("--json", dest="json_out", type=Path, default=None)
    args = parser.parse_args(argv)

    sheets = [_load(p) for p in sorted(args.beatsheets.glob("*.json"))]
    if not sheets:
        print(f"No beat sheets found in {args.beatsheets}")
        return 1
    registry = _load(args.registry)
    shotlist = build_shotlist(sheets, registry)

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(shotlist), encoding="utf-8")
        print(f"wrote {args.markdown}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(shotlist, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json_out}")

    totals = shotlist["totals"]
    print(
        f"{totals['characters']} characters, {totals['distinct_clips']} distinct clips, "
        f"{totals['clip_assignments']} clip assignments"
    )
    if shotlist["unused_actions"]:
        names = ", ".join(shotlist["unused_actions"])
        print(f"unused registry actions ({len(shotlist['unused_actions'])}): {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
