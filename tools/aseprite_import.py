"""Convert a real Aseprite/LibreSprite CLI export (spritesheet JSON + PNG)
into a layer entry for our scene JSON format.

Plain functions, no classes -- matches env_pipeline/environment.py's style.
`import_layer(json_path, ...)` is the entry point other code should call.

Expected CLI export, produced via:
    <tool> -b sprite.ase --format json-array --sheet sheet.png --data sheet.json \
        --list-tags --list-layers

Schema observed from a REAL LibreSprite 1.2-dev export (inspected directly,
not assumed -- see godot_project/AnimationEngine.gd module docstring / the
Phase 1/2 report for the exact fixtures this was verified against):

    {
      "frames": [
        {"filename": "sprite 0.ase",
         "frame": {"x":0,"y":0,"w":16,"h":16},
         "rotated": false, "trimmed": false,
         "spriteSourceSize": {"x":0,"y":0,"w":16,"h":16},
         "sourceSize": {"w":16,"h":16},
         "duration": 80},
        ...
      ],
      "meta": {
        "app": "https://github.com/LibreSprite/LibreSprite/",
        "version": "1.2-dev",
        "image": "sheet.png",
        "format": "RGBA8888" | "I8",   // I8 = indexed/paletted sheet
        "size": {"w":64,"h":16},
        "scale": "1",
        "frameTags": [
          {"name": "flicker", "from": 0, "to": 3, "direction": "pingpong"}
        ],
        "layers": [
          {"name": "torch", "opacity": 255, "blendMode": "normal"}
        ]
      }
    }

Real, source-confirmed quirks this importer accounts for:
  - `meta.frameTags` is empty (`[]`) for untagged sprites -- no implicit tag
    is written to the file. We synthesize one ourselves, matching Aseprite's
    own `create_loop_tag` fallback (`loop_tag.h`): a single whole-sprite
    "default" tag, forward direction, repeat 0.
  - Direction strings from LibreSprite 1.2-dev are "forward"/"reverse"/
    "pingpong" (no underscore, and this build's doc::AniDir enum has only
    those three values -- no ping_pong_reverse; that's an Aseprite-only
    4th mode added after LibreSprite's fork point). We normalize incoming
    direction strings to "forward"/"reverse"/"ping_pong"/"ping_pong_reverse"
    so the scene JSON schema is stable regardless of which tool produced the
    export, and pass "ping_pong_reverse" through untranslated since it can
    appear in real Aseprite (not LibreSprite) exports.
  - Without `--split-layers`, LibreSprite's exporter flattens all visible
    layers into one composited frame per animation frame, and `meta.layers`
    only lists top-level layers (nested group children were not observed in
    exported JSON from this build, confirmed by direct experiment). We still
    parse `layers[].group` defensively if present, for forward compatibility
    with real Aseprite exports (whose documented schema does include it) --
    but we do not depend on this build ever emitting it.
  - `meta.format == "I8"` means the sheet PNG is a paletted (mode "P") PNG,
    not flattened RGBA. We surface this via `is_indexed` in the returned
    layer entry, plus a `palette` (list of [r,g,b,a]) resolved from the
    PNG's own PLTE/tRNS chunks via Pillow, so a caller can either trust the
    PNG decoder to have already expanded pixels to RGBA (which Godot's own
    PNG loader does) or keep the palette around for a future runtime
    palette-swap.
"""
import json
import os

DIRECTION_ALIASES = {
    "forward": "forward",
    "reverse": "reverse",
    "pingpong": "ping_pong",
    "ping_pong": "ping_pong",
    "pingpongreverse": "ping_pong_reverse",
    "ping_pong_reverse": "ping_pong_reverse",
    "pingpong_reverse": "ping_pong_reverse",
}

# Aseprite blendMode string -> Godot CanvasItemMaterial.BLEND_MODE_* enum value.
# (Godot only has 4 built-in composite blend modes; anything without a direct
# equivalent falls back to MIX/normal -- listed explicitly rather than
# silently defaulting, so a caller can tell "mapped" from "unsupported".)
BLEND_MODE_TO_GODOT = {
    "normal": 0,       # BLEND_MODE_MIX
    "multiply": 3,      # BLEND_MODE_MUL
    "screen": 0,        # no native match -> falls back to normal (documented gap)
    "overlay": 0,
    "darken": 0,
    "lighten": 1,       # BLEND_MODE_ADD is the closest built-in for lightening
    "color_dodge": 1,
    "color_burn": 0,
    "hard_light": 0,
    "soft_light": 0,
    "difference": 2,    # BLEND_MODE_SUB is the closest built-in for difference-like darkening
    "exclusion": 2,
    "hsl_hue": 0,
    "hsl_saturation": 0,
    "hsl_color": 0,
    "hsl_luminosity": 0,
}

UNMAPPED_BLEND_MODES = {"screen", "overlay", "darken", "color_burn", "hard_light",
                         "soft_light", "hsl_hue", "hsl_saturation", "hsl_color",
                         "hsl_luminosity"}


def _normalize_direction(direction: str) -> str:
    key = direction.replace("-", "").replace("_", "").lower()
    return DIRECTION_ALIASES.get(direction, DIRECTION_ALIASES.get(key, "forward"))


def load_export(json_path: str) -> dict:
    """Load and parse a raw Aseprite/LibreSprite CLI export JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_cels(export: dict) -> list:
    """Flatten export['frames'] into our cel schema: [{x,y,w,h,duration_ms}]."""
    cels = []
    for frame in export.get("frames", []):
        rect = frame["frame"]
        cels.append({
            "x": rect["x"],
            "y": rect["y"],
            "w": rect["w"],
            "h": rect["h"],
            "duration_ms": frame.get("duration", 100),
        })
    return cels


def build_tags(export: dict) -> list:
    """Build our tag schema from meta.frameTags, synthesizing an implicit
    whole-sprite "default" tag (matching Aseprite's create_loop_tag fallback,
    loop_tag.h) when the export has none."""
    meta = export.get("meta", {})
    raw_tags = meta.get("frameTags", [])
    frame_count = len(export.get("frames", []))

    if not raw_tags:
        if frame_count == 0:
            return []
        return [{
            "name": "default",
            "from": 0,
            "to": frame_count - 1,
            "direction": "forward",
            "repeat": 0,
        }]

    tags = []
    for tag in raw_tags:
        tags.append({
            "name": tag["name"],
            "from": tag["from"],
            "to": tag["to"],
            "direction": _normalize_direction(tag.get("direction", "forward")),
            "repeat": tag.get("repeat", 0),
        })
    return tags


def resolve_palette(png_path: str) -> list:
    """If png_path is a paletted (mode 'P') PNG, return its palette resolved
    to RGBA as a list of [r,g,b,a] entries (alpha from the tRNS chunk when
    present, 255 otherwise). Returns [] for non-indexed images or if Pillow
    is unavailable."""
    try:
        from PIL import Image
    except ImportError:
        return []

    img = Image.open(png_path)
    if img.mode != "P":
        return []

    raw_palette = img.getpalette() or []
    rgb_entries = [tuple(raw_palette[i:i + 3]) for i in range(0, len(raw_palette), 3)]

    alphas = {}
    info_trns = img.info.get("transparency")
    if isinstance(info_trns, (bytes, bytearray)):
        for idx, a in enumerate(info_trns):
            alphas[idx] = a
    elif isinstance(info_trns, int):
        # Pillow collapses a single-entry tRNS chunk (only one fully
        # transparent palette index, no partial-alpha entries -- LibreSprite's
        # own exported sheets use this form) down to a bare int instead of a
        # byte array. Observed directly on a real indexed CLI export.
        alphas[info_trns] = 0

    palette = []
    for idx, (r, g, b) in enumerate(rgb_entries):
        palette.append([r, g, b, alphas.get(idx, 255)])
    return palette


def _resolve_sheet_path(base_dir: str, image_rel: str) -> str:
    """meta.image is a real quirk: it's written relative to whatever
    directory the CLI was *invoked from*, not relative to --data's own
    output location (confirmed by direct experiment -- a --data path of
    testsrc/sheet.json run from the parent dir produces meta.image
    "testsrc/sheet.png", not "sheet.png"). So resolve defensively: try
    the path as given relative to the JSON's directory first, then fall
    back to just its basename in that same directory."""
    if not image_rel:
        return None
    candidate = os.path.join(base_dir, image_rel)
    if os.path.exists(candidate):
        return candidate
    fallback = os.path.join(base_dir, os.path.basename(image_rel))
    if os.path.exists(fallback):
        return fallback
    return candidate  # neither exists; return the primary guess so callers get a clear error


def import_layer(json_path: str, png_path: str = None, name: str = None,
                  depth: float = 1.0) -> dict:
    """Convert one Aseprite/LibreSprite CLI export into a scene-JSON layer
    entry. `png_path` defaults to meta.image resolved relative to json_path's
    directory (matching how the CLI writes --data/--sheet paths). `name`
    defaults to the first entry in meta.layers, falling back to the export's
    base filename."""
    export = load_export(json_path)
    meta = export.get("meta", {})
    base_dir = os.path.dirname(os.path.abspath(json_path))

    if png_path is None:
        image_rel = meta.get("image", "")
        png_path = _resolve_sheet_path(base_dir, image_rel)

    layers_meta = meta.get("layers", [])
    first_layer = layers_meta[0] if layers_meta else {}

    layer_name = name or first_layer.get("name") or os.path.splitext(os.path.basename(json_path))[0]
    blend_mode_str = first_layer.get("blendMode", "normal")
    is_indexed = meta.get("format") == "I8"

    spritesheet_rel = meta.get("image", os.path.basename(png_path) if png_path else "")

    entry = {
        "name": layer_name,
        "depth": depth,
        "spritesheet": spritesheet_rel,
        "cels": build_cels(export),
        "tags": build_tags(export),
        "blend_mode": blend_mode_str,
        "godot_blend_mode": BLEND_MODE_TO_GODOT.get(blend_mode_str, 0),
        "is_indexed": is_indexed,
    }

    group = first_layer.get("group")
    if group:
        entry["group"] = group

    if is_indexed and png_path and os.path.exists(png_path):
        palette = resolve_palette(png_path)
        if palette:
            entry["palette"] = palette

    return entry


def import_layers_from_group(json_paths: list, depths: dict = None, groups: dict = None) -> list:
    """Convenience wrapper: import several CLI exports (e.g. one per split
    layer/group member) into a list of scene-JSON layer entries in one call.
    `depths`/`groups` are optional {layer_name: value} overrides applied
    after import (useful since LibreSprite's own export doesn't always carry
    depth or nested group info)."""
    depths = depths or {}
    groups = groups or {}
    entries = []
    for path in json_paths:
        entry = import_layer(path)
        if entry["name"] in depths:
            entry["depth"] = depths[entry["name"]]
        if entry["name"] in groups:
            entry["group"] = groups[entry["name"]]
        entries.append(entry)
    return entries


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python aseprite_import.py <export.json> [output.json]")
        sys.exit(1)

    result = import_layer(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Wrote {output_path}")
    else:
        print(json.dumps(result, indent=2))
