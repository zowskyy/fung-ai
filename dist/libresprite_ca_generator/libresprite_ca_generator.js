// ============================================================================
// "Generate CA Pattern" — LibreSprite script command
// ============================================================================
//
// Paints real output from our cellular-automaton cave generator
// (fungaiV2_extracted/fung_ai_v2.py, function `generate`, rule B3/S23 —
// same engine the rest of this project uses, not reimplemented here) into
// the active LibreSprite cel: wall cells get one color, floor cells another.
//
// INSTALL (real LibreSprite scripting, per SCRIPTING.md + testing against
// the actual v1.2-dev Windows build — see research/aseprite_notes.md for
// exactly what differed from the docs):
//   1. In LibreSprite, run the "Open Scripts Folder" command
//      (File > Scripts > Open Scripts Folder, or app.command.OpenScriptsFolder()),
//      which is %APPDATA%\LibreSprite\scripts on Windows.
//   2. Copy this file into that folder.
//   3. Run "Rescan Scripts" (app.command.RescanScripts()). This file's name
//      then appears as a runnable entry under File > Scripts.
//   4. Open (or create) a sprite, then run "libresprite_ca_generator" from
//      the Scripts menu — that is the "Generate CA Pattern" command.
//
// WHY THE CA DATA IS EMBEDDED, NOT SHELLED-OUT OR FILE-READ AT RUNTIME:
//   The plan's ideal was: shell out to `python fung_ai_v2.py generate ...`
//   from the script and parse its JSON. LibreSprite's JS engine (a stripped
//   V8 embed, globals are only `app`, `storage`, `ColorMode` — confirmed by
//   enumerating them at runtime, not assumed from SCRIPTING.md, which is
//   itself out of date: e.g. it documents `command`/`pixelColor` as top-level
//   globals, but in the real v1.2-dev build they live at `app.command` /
//   `app.pixelColor`) has NO subprocess/exec/spawn capability anywhere in
//   that surface. `storage.fetch(url, key)` exists and *looks* like it could
//   load a local pre-generated JSON file via a `file://` URL, but tested
//   directly against a real file it never actually populates local content
//   (`storage.get(key)` stays in a permanently-pending state — reproduced
//   over 300 x 20ms yield cycles). So per the plan's own fallback clause,
//   this script imports a PRE-GENERATED CA output file — but embeds it as a
//   literal below rather than re-attempting the same broken local-fetch path,
//   since that path is real and demonstrably non-functional in this build.
//
// The CA_DATA below is the UNMODIFIED, VERBATIM output of:
//   python fung_ai_v2.py generate --rule B3/S23 --width 40 --height 30 \
//     --ticks 12 --seed 2026
// run directly against fungaiV2_extracted/fung_ai_v2.py on 2026-08-14.
// grid[y][x] === 1 -> wall cell, 0 -> floor cell (thresholded at >= 0.5,
// matching the engine's own float grid convention).
// ============================================================================

(function () {
  "use strict";

  var CA_DATA = {
    rule: "B3/S23",
    width: 40,
    height: 30,
    ticks: 12,
    seed: 2026,
    coverage: 0.1850000023841858,
    playable: true,
    density_used: 0.45,
    grid: [
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1,1,0,0],
      [1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,1],
      [1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1,1,0,0,0,1,1],
      [0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,1,0,1,0,1,0,1,1,1],
      [0,0,1,1,1,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,1,1,0,1,1,0,0],
      [0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
      [0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0],
      [1,0,0,0,0,0,0,0,1,1,1,0,0,0,0,1,1,0,0,0,1,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0,0,0,1],
      [1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1],
      [1,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0],
      [0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,1,0,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,0,0],
      [0,0,0,0,0,1,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,1,0],
      [0,0,0,0,1,1,1,0,1,1,0,0,0,1,1,1,0,0,0,0,1,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,1,0,0],
      [0,0,0,0,1,0,1,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,1,0,0],
      [0,0,0,0,0,1,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,1,1,0,0,1,0,0],
      [0,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,0,1,1],
      [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0],
      [0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,1,0],
      [0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1],
      [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
      [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
      [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,1,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
      [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,1,0,0,1,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
      [1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],
      [1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
      [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,1,1,0]
    ]
  };

  // CLI/headless verification fallback: no interactive doc is "active" in
  // LibreSprite's `-b` batch mode (app.activeSprite/app.activeImage stay
  // `undefined` there even after a file is passed on the command line or
  // loaded via app.open() — reproduced directly, not assumed; see
  // research/aseprite_notes.md). These paths are only used when there is no
  // real active sprite, i.e. when this script is invoked headlessly via
  // `libresprite --script` for automated verification, rather than from the
  // Scripts menu on an already-open sprite (the normal interactive case).
  var VERIFY_INPUT_PATH =
    "C:/Users/thewi/OneDrive/Desktop/fung.us/extensions/ca_generator_blank.png";
  var VERIFY_OUTPUT_PATH =
    "C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/imported_assets/ca_generated/ca_pattern.ase";

  function paintGrid(image, grid, wallColor, floorColor) {
    for (var y = 0; y < grid.length; y++) {
      var row = grid[y];
      for (var x = 0; x < row.length; x++) {
        image.putPixel(x, y, row[x] === 1 ? wallColor : floorColor);
      }
    }
  }

  function generateCaPattern() {
    var wallColor = app.pixelColor.rgba(60, 56, 54, 255);    // dark stone (wall)
    var floorColor = app.pixelColor.rgba(214, 188, 140, 255); // tan (floor)

    var sprite = app.activeSprite;
    var headlessDoc = null;

    if (!sprite) {
      // Headless verification path (see comment above).
      headlessDoc = app.open(VERIFY_INPUT_PATH);
      sprite = headlessDoc.sprite;
    }

    if (sprite.width !== CA_DATA.width || sprite.height !== CA_DATA.height) {
      sprite.resize(CA_DATA.width, CA_DATA.height);
    }

    var layer = sprite.layer(0);
    var cel = layer.cel(0);
    var image = cel.image;

    paintGrid(image, CA_DATA.grid, wallColor, floorColor);

    console.log(
      "Generate CA Pattern: painted " + CA_DATA.width + "x" + CA_DATA.height +
      " cells (rule=" + CA_DATA.rule + ", ticks=" + CA_DATA.ticks +
      ", seed=" + CA_DATA.seed + ", coverage=" + CA_DATA.coverage +
      ", playable=" + CA_DATA.playable + ") into the active cel."
    );

    if (headlessDoc) {
      sprite.saveAs(VERIFY_OUTPUT_PATH, false);
      console.log("Generate CA Pattern: saved verification sprite to " + VERIFY_OUTPUT_PATH);
    }
  }

  generateCaPattern();
})();
