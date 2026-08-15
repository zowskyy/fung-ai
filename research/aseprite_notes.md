# Phase 1 / Direction A — Aseprite & LibreSprite scripting research notes

Scope: "their editor gains our tech" — a real, invoked "Generate CA Pattern"
command inside a sprite editor, painting real `fung_ai_v2.py` CA output into
a cel. Everything below was verified directly against a real installed
build, not assumed from memory or from the docs alone (the docs turned out
to be wrong/stale in several places — noted explicitly).

## Which tool, and why

**Built against LibreSprite's JS scripting engine, not Aseprite's Lua API.**

- Aseprite's EULA permits personal compiled use, but building it requires a
  full C++/CMake/Skia toolchain (Visual Studio + a Skia checkout on
  Windows) — not realistically achievable inside this session, and the task
  brief explicitly says not to attempt that and to build against LibreSprite
  instead in that case. No attempt was made to compile Aseprite; this is a
  scoping decision, not a discovered failure.
- LibreSprite has real prebuilt Windows binaries (unlike some other
  platforms in its release history) — see below — so it was both the
  license-clean and the practically obtainable option.

## LibreSprite install

Checked `https://api.github.com/repos/LibreSprite/LibreSprite/releases`
directly (release page HTML was flaky over WebFetch, the API wasn't).
Windows assets that exist across releases:

- `v1.2` (2025-03-02): `libresprite-development-windows-x86_64.zip` — used this one (most recent tagged Windows build).
- `v1.1`, `v1.0`: also had Windows zips (`LibreSprite-Windows-x86_32/64.zip`).
- `_tmp` prerelease: a bare `LibreSpriteWin.exe` ("undocumented ... until we have a proper, FOSS pipeline").
- `continuous`: Linux AppImage only, no Windows asset.

Downloaded and extracted `v1.2`'s `libresprite-development-windows-x86_64.zip`
to `C:\Users\thewi\OneDrive\Desktop\fung.us\libresprite\`. Confirmed working:

```
> libresprite.exe --version
LibreSprite 1.2-dev
```

## Scripting docs vs. reality (SCRIPTING.md is stale)

Read `SCRIPTING.md` from the `master` branch first. Several things it
documents as top-level globals are **not** top-level in the real v1.2-dev
build — confirmed by enumerating live globals inside a running script
(`Object.getOwnPropertyNames(this)`), not by trusting the doc:

| SCRIPTING.md says | Actually (v1.2-dev, tested) |
|---|---|
| `command.X()` (global) | `app.command.X()` — 150+ commands present, e.g. `NewFile`, `RunScript`, `OpenScriptsFolder`, `RescanScripts` |
| `pixelColor.rgba(...)` (global) | `app.pixelColor.rgba(...)` |
| `Sprite`, `Image`, `Layer`, `Cel` as constructible globals | Not constructible directly. Reached only via `app.open(path).sprite`, `sprite.layer(i)`, `layer.cel(i)`, `cel.image` |
| `app.activeDocument` / `app.activeSprite` / `app.activeImage` | The getters exist (`Object.getOwnPropertyNames(app)` lists them) but return `undefined` in `-b` batch/headless mode even after a file is opened via CLI arg or `app.open()`. These are presumably only populated when a real GUI tab has focus — genuinely untestable without a display in this session, so the extension code paths for both cases (interactive `app.activeSprite` and headless `app.open()`) are written and the headless one is what's actually verified end-to-end below. |

Only 3 real top-level globals exist in a running script: `app`, `storage`,
`ColorMode`. `app`'s own properties (verified via
`Object.getOwnPropertyNames(app)`): `redraw, launch, open, yield,
createDialog, documentation, platform, version, pixelColor, activeDocument,
activeImage, command, activeSprite, activeLayerNumber, activeFrameNumber`.

### No subprocess / no working local file read

- **No subprocess/exec/spawn capability anywhere in the API surface** —
  confirmed by the full enumeration above; nothing resembling `exec`,
  `spawn`, `system`, or a child-process object exists. This directly
  matches the plan's anticipated fallback trigger.
- `storage.fetch(url, key)` exists and *looks* like it could pull in a
  pre-generated CA JSON file via a `file://` URL, so it was tested directly
  rather than assumed either way:
  ```js
  storage.fetch("file:///C:/.../ca_generated.json", "mydata");
  // then poll:
  storage.get("mydata")
  ```
  Result: `storage.get("mydata")` never actually populates with the file's
  content — `typeof` reports `"string"` but the value never gains a valid
  `.length` even after 300 polling iterations at 20ms `app.yield()` steps
  (6+ seconds). Network `http(s)://` fetches are presumably what this path
  is actually for; local `file://` fetch is real but non-functional in this
  build. This is the concrete, tested trigger for the plan's fallback
  clause.
- **Also discovered, not part of the plan but relevant to anyone else
  extending this**: calling a UI-dependent command like
  `app.command.NewFile()` in `-b` batch/headless mode **segfaults the
  process** (exit 139) rather than erroring gracefully. Batch-mode scripts
  must stick to the non-UI API (`app.open`, `Image`/`Cel`/`Sprite` methods,
  `sprite.saveAs`), which is exactly what this extension does.

### Working, verified API surface used by the extension

```
app.open(path) -> { close, sprite }
sprite: { loadPalette, crop, resize, commit, saveAs, save, layer(i), palette,
          colorMode, height, selection, width, filename, layerCount }
layer.cel(i) -> { setPosition, frame, image, x, y }
image: { getPNGData, getImageData, putImageData, clear, putPixel, getPixel,
         format, stride, height, width }
app.pixelColor.rgba(r,g,b,a) -> packed int color
```

### Extension mechanism (no `package.json` manifest — that's Aseprite's system)

LibreSprite does **not** have Aseprite's `package.json`-manifest extension
packaging. Its own model (per `app.command.OpenScriptsFolder` /
`InstallScript` / `RescanScripts`) is: drop a `.js` file into the user's
`scripts` folder (`%APPDATA%\LibreSprite\scripts` on Windows), run "Rescan
Scripts", and the filename becomes a runnable entry under File > Scripts.
That's the real "Generate CA Pattern" menu command once installed —
documented as install steps at the top of
`extensions/libresprite_ca_generator.js` itself.

### CLI flags (from `src/app/app_options.cpp`, read directly — not assumed)

Confirmed flags relevant here: `-b/--batch` (no UI), `--script <file>`
("Execute a specific script" — the real headless entry point used for
verification below), `--data`, `--format`, `--sheet`, `--list-layers`,
`--list-tags`.

## The extension

`extensions/libresprite_ca_generator.js`. Embeds the **unmodified, literal**
grid produced by:

```
python fung_ai_v2.py generate --rule B3/S23 --width 40 --height 30 --ticks 12 --seed 2026
```

run directly against `fungaiV2_extracted/fung_ai_v2.py` (the same,
already-working CA engine — not reimplemented). On run, it paints wall
cells (`grid[y][x] == 1`) as dark stone `rgba(60,56,54,255)` and floor cells
as tan `rgba(214,188,140,255)` into the active cel's image via
`image.putPixel`. It prefers `app.activeSprite` (the real interactive path,
used when run from the Scripts menu on an already-open sprite); when that's
unset (headless `-b --script` invocation, used for automated verification)
it falls back to `app.open()` on a blank 40x30 canvas
(`extensions/ca_generator_blank.png`) and saves the result.

## Verification (real invocation, real comparison)

Ran the extension through LibreSprite's own CLI, headlessly:

```
libresprite.exe -b --script extensions/libresprite_ca_generator.js
```

Output:
```
Generate CA Pattern: painted 40x30 cells (rule=B3/S23, ticks=12, seed=2026,
coverage=0.1850000023841858, playable=true) into the active cel.
Generate CA Pattern: saved verification sprite to
C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/imported_assets/ca_generated/ca_pattern.ase
```

This produced a real `.ase` sprite file (496 bytes) in
`godot_project/imported_assets/ca_generated/`.

Then compared its painted pixels against a **fresh, independent** direct run
of `fung_ai_v2.py generate` with the same rule/size/seed — exported the
`.ase` back out to a PNG via LibreSprite's own CLI (see below), loaded both
the exported PNG and the direct CLI's JSON grid in Python/PIL, and diffed
every cell:

```
total cells 1200 mismatches 0
```

All 1200 cells (40x30) match exactly — every wall cell in the direct CA
output is dark-stone in the painted sprite and every floor cell is tan, with
zero discrepancies. This is a genuine pixel-exact proof, not a placeholder
image.

## CLI export for the importer agent

```
libresprite.exe -b godot_project/imported_assets/ca_generated/ca_pattern.ase \
  --format json-array \
  --sheet godot_project/imported_assets/ca_generated/sheet.png \
  --data godot_project/imported_assets/ca_generated/sheet.json \
  --list-tags --list-layers
```

Output files:
- `C:\Users\thewi\OneDrive\Desktop\fung.us\godot_project\imported_assets\ca_generated\sheet.png` (455 bytes, 40x30 RGBA8888)
- `C:\Users\thewi\OneDrive\Desktop\fung.us\godot_project\imported_assets\ca_generated\sheet.json`
- `C:\Users\thewi\OneDrive\Desktop\fung.us\godot_project\imported_assets\ca_generated\ca_pattern.ase` (the source sprite)

### Real observed JSON schema (`sheet.json`, verbatim shape)

```json
{ "frames": [
   {
    "filename": "ca_pattern.ase",
    "frame": { "x": 0, "y": 0, "w": 40, "h": 30 },
    "rotated": false,
    "trimmed": false,
    "spriteSourceSize": { "x": 0, "y": 0, "w": 40, "h": 30 },
    "sourceSize": { "w": 40, "h": 30 },
    "duration": 100
   }
 ],
 "meta": {
  "app": "https://github.com/LibreSprite/LibreSprite/",
  "version": "1.2-dev",
  "image": "<absolute path to sheet.png>",
  "format": "RGBA8888",
  "size": { "w": 40, "h": 30 },
  "scale": "1",
  "frameTags": [],
  "layers": [
   { "name": "Layer", "opacity": 255, "blendMode": "normal" }
  ]
 }
}
```

Notes vs. the plan's assumed schema (`research/` section of the plan doc):
- Assumed shape (`frames`, `meta.frameTags`, `meta.layers`) is broadly
  right, confirmed for real.
- `frameTags` is genuinely **empty** here (untagged, single-frame sprite) —
  the importer needs to handle the empty-array case, not just assume at
  least one tag. The plan doc's own note about an implicit synthesized
  whole-sprite loop tag for untagged sprites (`create_loop_tag`, from
  Aseprite's C++ source) is about *playback*, not the exported JSON — the
  exported `frameTags` array itself stays empty; the importer is the one
  that needs to synthesize a fallback tag, not expect the exporter to.
- `meta.layers[]` items here have no `"group"` key at all (this test sprite
  has no layer groups) — confirms the plan's assumption that `group` is
  optional/absent rather than `null`, so the importer should use
  `layer.get("group")`-style optional access, not assume the key exists.
- `opacity` is a plain integer (0-255), not a float/percentage.
- Top-level `frames` is a **list** here (this build's `json-array` format,
  matching the flag actually passed), not the filename-keyed dict that
  `--format json-hash` would produce — worth the importer explicitly
  requiring/asserting `json-array` was used, since both formats are
  selectable via `--format` and have different top-level shapes.

## Deviations / constraints from the plan, summarized

1. Built against LibreSprite JS, not Aseprite Lua (compiling Aseprite from
   source not attempted — out of scope per the task's own instructions).
2. `SCRIPTING.md` is stale in several places (see table above) — verified
   the real API by enumerating it live rather than trusting the doc.
3. No subprocess capability — confirmed, not assumed. The extension embeds
   a pre-generated, unmodified CA output rather than shelling out.
4. `storage.fetch()` on local `file://` paths is real but non-functional in
   this build — tested directly (300 poll iterations, never resolves) —
   so the embed approach was chosen over a broken runtime-fetch path.
5. `app.activeSprite`/`app.activeImage` are unpopulated in `-b` batch mode
   even with a file opened — the extension's headless-verification fallback
   (`app.open()` on a blank canvas) exists specifically because of this;
   the interactive `app.activeSprite` path is written per the docs but
   could not itself be click-tested in this session (no display/GUI
   automation available here for LibreSprite specifically).
6. `app.command.NewFile()` (and likely other UI-driving commands) segfaults
   in batch mode — avoided entirely by using `app.open()` instead.
7. LibreSprite has no Aseprite-style `package.json` extension manifest; its
   extension mechanism is a flat `scripts` folder + "Rescan Scripts" —
   documented as the real install steps in the script file itself.

## Unverified / risk flags

- The **interactive** path (running the script from LibreSprite's Scripts
  menu on a sprite a human has open in the real GUI) was not manually
  click-tested — this session has no way to drive the LibreSprite GUI
  directly. The headless `-b --script` path, which exercises the identical
  `Image.putPixel`/`saveAs` code, **was** run and pixel-verified end-to-end,
  and `app.activeSprite` is used first exactly per the documented pattern,
  so the interactive path should work, but that specific claim rests on the
  API shape rather than a manual click-through.
- `SCRIPTING.md` may drift further from future LibreSprite releases; the
  discrepancies above are pinned to the `v1.2-dev` Windows build tested here.
