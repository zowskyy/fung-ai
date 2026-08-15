# aseprite_ca_generator — NOT BUILT (placeholder only)

**This package does not exist yet. Nothing in this folder is a working
Aseprite extension.** It is a placeholder documenting scope for future work,
kept separate from the real, tested deliverable at
`dist/libresprite_ca_generator/` so the two are never confused.

## Why there's nothing here

The original plan called for an Aseprite Lua extension
(`extensions/aseprite_ca_generator/` — `package.json` + `main.lua`) mirroring
the real LibreSprite JS script. That was **not attempted**: Aseprite's EULA
permits personal compiled use, but building Aseprite from source requires a
full C++/CMake/Skia toolchain (Visual Studio + a Skia checkout on Windows),
which was not feasible in the session that did this work, and no
pre-existing Aseprite installation was available to script against instead.
This is a scoping decision made explicitly at the time, not a build that was
attempted and failed.

Concretely, none of the following exist:

- No `main.lua` or any Lua code.
- No `package.json` extension manifest.
- No verification of any kind against a real Aseprite instance.
- No confirmation that Aseprite's Lua `Image`/`Cel` API even matches the
  LibreSprite JS API closely enough for a straight port (they're related
  but independently maintained; assume nothing carries over without
  re-checking against Aseprite's real `api/` docs and a real running copy).

## What a real version would need, if built later

1. A real Aseprite installation (compiled from source under its EULA, or
   otherwise obtained) to script and test against — not assumed from docs.
2. Aseprite's real Lua scripting API, read from its own `api/` reference
   and verified live (the LibreSprite work in this project found its own
   docs, `SCRIPTING.md`, to be stale in several places — assume Aseprite's
   may be too, and check).
3. A `package.json` manifest (Aseprite's actual extension packaging system,
   unlike LibreSprite's flat-scripts-folder model) plus `main.lua`
   registering a menu command, most likely via `Sprite:newCel` / `Image`
   pixel-write APIs analogous to the LibreSprite script's
   `image.putPixel` usage.
4. The same kind of pixel-exact verification done for the LibreSprite
   package (`dist/libresprite_ca_generator/README.md`) — a real invocation,
   compared cell-by-cell against a fresh direct run of `fung_ai_v2.py`.
5. Packaging as a real `.aseprite-extension` (a zip of the manifest +
   script), which is the actual Aseprite installable format — distinct from
   what's needed for LibreSprite.

None of the above was done this pass. Treat this folder as a scope note,
not a deliverable.
