"""Build Godot ScenePlan .tres resources from JSON beat sheets.

Why this exists
---------------
The film's beats are authored as prose breakdowns (``scenes/*_breakdown.md``),
which are the human-readable source of truth. Godot needs them as ``ScenePlan``
resources. Hand-writing 60+ beats of ``.tres`` is error-prone and unreviewable,
so beats are captured once as JSON (``scenes/beatsheets/*.json``) and this
module generates the ``.tres`` deterministically.

It also carries a Python mirror of ``ScenePlanValidator`` (the addon's GDScript
authoring validator) so plans can be proven error-free in CI, where no Godot
binary exists. The mirror deliberately reproduces only the ERROR-severity rules
-- those are the ones that make a plan unrunnable. Warning-level rules
(unreachable beats, unknown actors) are reported separately and don't fail the
gate, matching the addon's contract that "valid" means "no ERROR issues".

Keeping the two validators in sync matters: if
``addons/scene_animator/editor/validators/scene_plan_validator.gd`` grows a new
ERROR code, add it here too, or CI will pass plans the editor rejects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ADDON_DATA = "res://addons/scene_animator/data"

# Beat type -> (script path, ext_resource id, {json_field: (tres_field, kind)}).
# `kind` drives serialization: sn=StringName, s=String, f=float, b=bool,
# np=NodePath. Fields absent from a beat sheet are simply not emitted, so the
# resource falls back to the @export default declared in GDScript.
BEAT_TYPES: dict[str, dict[str, Any]] = {
    "dialogue": {
        "script": f"{ADDON_DATA}/beats/dialogue_beat.gd",
        "ext_id": "dialogue",
        "fields": {
            "dialogue_id": ("dialogue_id", "sn"),
            "speaker_actor_id": ("speaker_actor_id", "sn"),
            "target_actor_id": ("target_actor_id", "sn"),
            "timeout_seconds": ("timeout_seconds", "f"),
        },
    },
    "action": {
        "script": f"{ADDON_DATA}/beats/action_beat.gd",
        "ext_id": "action",
        "fields": {
            "actor_id": ("actor_id", "sn"),
            "action_id": ("action_id", "sn"),
            "target_path": ("target_path", "np"),
            "wait_for_completion": ("wait_for_completion", "b"),
            "completion_event": ("completion_event", "sn"),
            "timeout_seconds": ("timeout_seconds", "f"),
        },
    },
    "camera": {
        "script": f"{ADDON_DATA}/beats/camera_beat.gd",
        "ext_id": "camera",
        "fields": {
            "camera_mode_id": ("camera_mode_id", "sn"),
            "focus_target_path": ("focus_target_path", "np"),
            "blend_seconds": ("blend_seconds", "f"),
        },
    },
    "wait": {
        "script": f"{ADDON_DATA}/beats/wait_beat.gd",
        "ext_id": "wait",
        "fields": {"duration_seconds": ("duration_seconds", "f")},
    },
    "move_to": {
        "script": f"{ADDON_DATA}/beats/move_to_beat.gd",
        "ext_id": "move_to",
        "fields": {
            "actor_id": ("actor_id", "sn"),
            "target_path": ("target_path", "np"),
            "arrival_radius": ("arrival_radius", "f"),
            "locomotion_mode": ("locomotion_mode", "s"),
            "timeout_seconds": ("timeout_seconds", "f"),
        },
    },
    "end": {
        "script": f"{ADDON_DATA}/beats/end_beat.gd",
        "ext_id": "end",
        "fields": {"completion_signal": ("completion_signal", "sn")},
    },
}

# Fields every beat inherits from SceneBeat.
BASE_FIELDS: dict[str, tuple[str, str]] = {
    "beat_id": ("beat_id", "sn"),
    "display_name": ("display_name", "s"),
    "enabled": ("enabled", "b"),
    "next_beat_id": ("next_beat_id", "sn"),
    "failure_beat_id": ("failure_beat_id", "sn"),
    "note": ("note", "s"),
}

# Beats that must name an actor, and which JSON field carries it. Mirrors
# ScenePlanValidator._check_actor_refs.
ACTOR_REQUIRED: dict[str, str] = {
    "action": "actor_id",
    "move_to": "actor_id",
}


class BuildError(Exception):
    """Raised when a beat sheet cannot be turned into a resource at all."""


@dataclass
class Issue:
    severity: str  # "ERROR" | "WARNING"
    code: str
    message: str
    beat_id: str = ""

    def __str__(self) -> str:
        where = f" [{self.beat_id}]" if self.beat_id else ""
        return f"{self.severity} {self.code}{where}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "WARNING"]

    @property
    def is_valid(self) -> bool:
        """A plan is valid when it has no ERROR issues -- the addon's contract."""
        return not self.errors


# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------


def _quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _serialize(value: Any, kind: str) -> str:
    if kind == "sn":
        return "&" + _quote(value)
    if kind == "s":
        return _quote(value)
    if kind == "np":
        return f"NodePath({_quote(value)})"
    if kind == "b":
        return "true" if value else "false"
    if kind == "f":
        return f"{float(value)}"
    raise BuildError(f"Unknown field kind: {kind}")


def _emit_fields(target: dict, spec: dict[str, tuple[str, str]], lines: list[str]) -> None:
    for json_key, (tres_key, kind) in spec.items():
        if json_key in target:
            lines.append(f"{tres_key} = {_serialize(target[json_key], kind)}")


def build_tres(plan: dict) -> str:
    """Render a beat sheet dict as Godot ``.tres`` text.

    Only beat types present in the sheet get an ``ext_resource`` line, so the
    generated file stays as small as the plan actually needs.
    """
    beats = plan.get("beats", [])
    actors = plan.get("actors", [])
    if not beats:
        raise BuildError(f"Plan '{plan.get('plan_id', '?')}' declares no beats.")

    used_types: list[str] = []
    for beat in beats:
        btype = beat.get("type")
        if btype not in BEAT_TYPES:
            raise BuildError(
                f"Beat '{beat.get('beat_id', '?')}' has unknown type {btype!r}. "
                f"Known types: {', '.join(sorted(BEAT_TYPES))}"
            )
        if btype not in used_types:
            used_types.append(btype)

    ext: list[str] = [f'[ext_resource type="Script" path="{ADDON_DATA}/scene_plan.gd" id="1_plan"]']
    next_id = 2
    if actors:
        ext.append(
            f'[ext_resource type="Script" '
            f'path="{ADDON_DATA}/scene_actor_binding.gd" id="{next_id}_actor"]'
        )
        next_id += 1
    type_ext_id: dict[str, str] = {}
    for btype in used_types:
        eid = f"{next_id}_{BEAT_TYPES[btype]['ext_id']}"
        type_ext_id[btype] = eid
        ext.append(f'[ext_resource type="Script" path="{BEAT_TYPES[btype]["script"]}" id="{eid}"]')
        next_id += 1

    subs: list[str] = []
    actor_refs: list[str] = []
    for actor in actors:
        sub_id = f"Resource_actor_{actor['actor_id']}"
        actor_refs.append(sub_id)
        lines = [
            f'[sub_resource type="Resource" id="{sub_id}"]',
            'script = ExtResource("2_actor")',
        ]
        _emit_fields(
            actor,
            {
                "actor_id": ("actor_id", "sn"),
                "display_name": ("display_name", "s"),
                "required": ("required", "b"),
            },
            lines,
        )
        if actor.get("actor_path"):
            lines.append(f'actor_path = NodePath({_quote(actor["actor_path"])})')
        tags = actor.get("actor_tags") or []
        if tags:
            rendered = ", ".join(_quote(t) for t in tags)
            lines.append(f"actor_tags = Array[StringName]([{rendered}])")
        subs.append("\n".join(lines))

    beat_refs: list[str] = []
    for beat in beats:
        btype = beat["type"]
        sub_id = f"Resource_beat_{beat['beat_id']}"
        beat_refs.append(sub_id)
        lines = [
            f'[sub_resource type="Resource" id="{sub_id}"]',
            f'script = ExtResource("{type_ext_id[btype]}")',
        ]
        _emit_fields(beat, BASE_FIELDS, lines)
        _emit_fields(beat, BEAT_TYPES[btype]["fields"], lines)
        subs.append("\n".join(lines))

    load_steps = len(ext) + len(subs) + 1

    out: list[str] = [
        f'[gd_resource type="Resource" script_class="ScenePlan" load_steps={load_steps} format=3]',
        "",
        "\n".join(ext),
        "",
        "\n\n".join(subs),
        "",
        "[resource]",
        'script = ExtResource("1_plan")',
        f'plan_id = &{_quote(plan["plan_id"])}',
    ]
    if plan.get("display_name"):
        out.append(f'display_name = {_quote(plan["display_name"])}')
    if plan.get("description"):
        out.append(f'description = {_quote(plan["description"])}')
    if actor_refs:
        rendered = ", ".join(f'SubResource("{r}")' for r in actor_refs)
        out.append(f"actors = Array[Resource]([{rendered}])")
    rendered_beats = ", ".join(f'SubResource("{r}")' for r in beat_refs)
    out.append(f"beats = Array[Resource]([{rendered_beats}])")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# Validation (Python mirror of ScenePlanValidator's ERROR rules)
# --------------------------------------------------------------------------


def validate_plan(plan: dict, registry: dict | None = None) -> ValidationResult:
    """Check a beat sheet against the addon's authoring rules.

    ``registry`` is a capability registry dict (see build_capability_registry);
    when omitted, action/camera capability checks are skipped and reported as a
    warning, exactly as the GDScript validator does.
    """
    result = ValidationResult()
    add = result.issues.append

    if not plan.get("plan_id"):
        add(Issue("WARNING", "plan_id_missing", "Plan declares no plan_id."))

    beats = plan.get("beats", [])
    actors = plan.get("actors", [])

    if not beats:
        add(Issue("ERROR", "empty_plan", "Plan declares no beats and can never run."))
        return result
    if not any(b.get("enabled", True) for b in beats):
        add(Issue("ERROR", "no_enabled_beats", "Every beat is disabled; the plan can never start."))
    if not actors:
        add(Issue("WARNING", "no_actors", "Plan declares no actors."))

    actor_ids: set[str] = set()
    for actor in actors:
        aid = actor.get("actor_id", "")
        if not aid:
            add(Issue("ERROR", "actor_id_missing", "An actor binding declares no actor_id."))
            continue
        if aid in actor_ids:
            add(Issue("ERROR", "duplicate_actor_id", f"Actor id '{aid}' declared more than once."))
            continue
        actor_ids.add(aid)

    beat_ids: set[str] = set()
    for beat in beats:
        bid = beat.get("beat_id", "")
        if not bid:
            add(Issue("ERROR", "beat_id_missing", "Beat declares no beat_id."))
            continue
        if bid in beat_ids:
            add(
                Issue("ERROR", "duplicate_beat_id", f"Beat id '{bid}' declared twice.", bid)
            )
            continue
        beat_ids.add(bid)

    for beat in beats:
        bid = beat.get("beat_id", "")
        btype = beat.get("type", "")
        flow_checks = (
            ("next_beat_id", "dangling_next"),
            ("failure_beat_id", "dangling_failure"),
        )
        for flow_key, code in flow_checks:
            target = beat.get(flow_key, "")
            if target and target not in beat_ids:
                add(Issue("ERROR", code, f"{flow_key} references missing beat '{target}'.", bid))

        if btype == "dialogue":
            speaker = beat.get("speaker_actor_id", "")
            if not speaker:
                add(Issue("ERROR", "missing_speaker", "Dialogue beat declares no speaker.", bid))
            elif speaker not in actor_ids:
                add(Issue("WARNING", "unknown_actor", f"Unknown actor '{speaker}'.", bid))
            target = beat.get("target_actor_id", "")
            if target and target not in actor_ids:
                add(Issue("WARNING", "unknown_actor", f"Unknown actor '{target}'.", bid))
        elif btype in ACTOR_REQUIRED:
            actor_id = beat.get(ACTOR_REQUIRED[btype], "")
            if not actor_id:
                add(Issue("ERROR", "missing_actor", f"{btype} beat declares no actor.", bid))
            elif actor_id not in actor_ids:
                add(Issue("WARNING", "unknown_actor", f"Unknown actor '{actor_id}'.", bid))

    _validate_reachability(beats, result)

    if registry is None:
        add(Issue("WARNING", "no_capability_registry", "No registry; capability checks skipped."))
    else:
        _validate_capabilities(beats, registry, result)
    return result


def _validate_reachability(beats: list[dict], result: ValidationResult) -> None:
    start = next((b for b in beats if b.get("enabled", True)), None)
    if start is None:
        return
    by_id = {b["beat_id"]: b for b in beats if b.get("beat_id")}
    reachable = {start["beat_id"]}
    queue = [start]
    while queue:
        beat = queue.pop()
        for edge in (beat.get("next_beat_id", ""), beat.get("failure_beat_id", "")):
            if not edge or edge in reachable or edge not in by_id:
                continue
            reachable.add(edge)
            queue.append(by_id[edge])
    for beat in beats:
        bid = beat.get("beat_id", "")
        if beat.get("enabled", True) and bid and bid not in reachable:
            result.issues.append(
                Issue(
                    "WARNING",
                    "unreachable_beat",
                    "Beat is not reachable from the first beat.",
                    bid,
                )
            )


def _validate_capabilities(beats: list[dict], registry: dict, result: ValidationResult) -> None:
    action_ids = {a["id"] for a in registry.get("actions", [])}
    camera_ids = {c["id"] for c in registry.get("camera_modes", [])}
    for beat in beats:
        bid = beat.get("beat_id", "")
        if beat.get("type") == "action":
            aid = beat.get("action_id", "")
            if aid not in action_ids:
                result.issues.append(
                    Issue("ERROR", "unknown_action", f"action_id '{aid}' is not registered.", bid)
                )
        elif beat.get("type") == "camera":
            cid = beat.get("camera_mode_id", "")
            if cid not in camera_ids:
                result.issues.append(
                    Issue(
                        "ERROR",
                        "unknown_camera_mode",
                        f"camera_mode_id '{cid}' is not registered.",
                        bid,
                    )
                )


# --------------------------------------------------------------------------
# Capability registry
# --------------------------------------------------------------------------


def build_capability_registry(registry: dict) -> str:
    """Render a capability registry dict as ``.tres`` text."""
    actions = registry.get("actions", [])
    cameras = registry.get("camera_modes", [])

    ext = [
        f'[ext_resource type="Script" '
        f'path="{ADDON_DATA}/scene_capability_registry.gd" id="1_registry"]'
    ]
    next_id = 2
    if actions:
        ext.append(
            f'[ext_resource type="Script" '
            f'path="{ADDON_DATA}/action_definition.gd" id="{next_id}_action"]'
        )
        action_ext = f"{next_id}_action"
        next_id += 1
    if cameras:
        ext.append(
            f'[ext_resource type="Script" '
            f'path="{ADDON_DATA}/camera_mode_definition.gd" id="{next_id}_camera"]'
        )
        camera_ext = f"{next_id}_camera"
        next_id += 1

    subs: list[str] = []
    action_refs: list[str] = []
    for action in actions:
        sub_id = f"Resource_action_{action['id']}"
        action_refs.append(sub_id)
        lines = [
            f'[sub_resource type="Resource" id="{sub_id}"]',
            f'script = ExtResource("{action_ext}")',
            f'id = &{_quote(action["id"])}',
        ]
        if action.get("display_name"):
            lines.append(f'display_name = {_quote(action["display_name"])}')
        if action.get("animation_state"):
            lines.append(f'animation_state = &{_quote(action["animation_state"])}')
        if action.get("motion_mode"):
            lines.append(f'motion_mode = {_quote(action["motion_mode"])}')
        subs.append("\n".join(lines))

    camera_refs: list[str] = []
    for camera in cameras:
        sub_id = f"Resource_camera_{camera['id']}"
        camera_refs.append(sub_id)
        lines = [
            f'[sub_resource type="Resource" id="{sub_id}"]',
            f'script = ExtResource("{camera_ext}")',
            f'id = &{_quote(camera["id"])}',
        ]
        if camera.get("display_name"):
            lines.append(f'display_name = {_quote(camera["display_name"])}')
        if "is_dynamic" in camera:
            lines.append(f'is_dynamic = {"true" if camera["is_dynamic"] else "false"}')
        if "requires_focus_target" in camera:
            lines.append(
                f'requires_focus_target = {"true" if camera["requires_focus_target"] else "false"}'
            )
        if "default_blend_seconds" in camera:
            lines.append(f'default_blend_seconds = {float(camera["default_blend_seconds"])}')
        subs.append("\n".join(lines))

    load_steps = len(ext) + len(subs) + 1
    out = [
        f'[gd_resource type="Resource" script_class="SceneCapabilityRegistry" '
        f"load_steps={load_steps} format=3]",
        "",
        "\n".join(ext),
        "",
        "\n\n".join(subs),
        "",
        "[resource]",
        'script = ExtResource("1_registry")',
    ]
    if action_refs:
        rendered = ", ".join(f'SubResource("{r}")' for r in action_refs)
        out.append(f"actions = Array[Resource]([{rendered}])")
    if camera_refs:
        rendered = ", ".join(f'SubResource("{r}")' for r in camera_refs)
        out.append(f"camera_modes = Array[Resource]([{rendered}])")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Generate a ScenePlan .tres from a beat sheet.")
    p_build.add_argument("beatsheet", type=Path)
    p_build.add_argument("output", type=Path)
    p_build.add_argument("--registry", type=Path, default=None)

    p_val = sub.add_parser("validate", help="Validate beat sheets without writing output.")
    p_val.add_argument("beatsheets", type=Path, nargs="+")
    p_val.add_argument("--registry", type=Path, default=None)

    p_reg = sub.add_parser("build-registry", help="Generate the capability registry .tres.")
    p_reg.add_argument("registry", type=Path)
    p_reg.add_argument("output", type=Path)

    args = parser.parse_args(argv)

    if args.command == "build-registry":
        registry = _load(args.registry)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(build_capability_registry(registry), encoding="utf-8")
        print(f"wrote {args.output}")
        return 0

    registry = _load(args.registry) if args.registry else None

    if args.command == "build":
        plan = _load(args.beatsheet)
        result = validate_plan(plan, registry)
        for issue in result.issues:
            print(issue)
        if not result.is_valid:
            print(f"REFUSING to build {plan.get('plan_id')}: {len(result.errors)} error(s).")
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(build_tres(plan), encoding="utf-8")
        print(f"wrote {args.output} ({len(plan['beats'])} beats)")
        return 0

    exit_code = 0
    for path in args.beatsheets:
        plan = _load(path)
        result = validate_plan(plan, registry)
        for issue in result.issues:
            print(f"{path.name}: {issue}")
        status = "OK" if result.is_valid else "FAIL"
        counts = f"{len(result.errors)} errors, {len(result.warnings)} warnings"
        print(f"{path.name}: {status} ({counts})")
        if not result.is_valid:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
