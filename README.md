# Fung Godot Toolkit

A free, open-source, offline-first Godot 4 editor plugin for procedural cave-level generation. Pick a recipe, generate diverse candidates, browse them, lock a seed, and export an editable `TileMapLayer` scene — no internet connection, accounts, or paid licenses required.

Ship the exported scenes in commercial games under the terms of the MIT license (see [LICENSE](LICENSE)).

## What it does

1. **Generate** — pick a built-in recipe (16 shipped, covering top-down rooms/caverns/mazes and side-view platformer-oriented caves), a seed, a map size, and a generation budget.
2. **Browse** — the plugin runs a local Python cellular-automata engine as a subprocess, non-blocking, and reports back a batch of candidate caves with metrics (walkable ratio, path length, loop count, branch count, open-space score) and readable tags.
3. **Export** — pick a candidate, point at a `TileSet`, and export a `TileMapLayer`-based Godot scene with spawn/exit markers and gameplay-marker placeholders, ready to open and edit.
4. **Library** — every export leaves behind a small reproducibility manifest (recipe, seed, metrics) so a level can be identified or regenerated later.

Same recipe + seed + map size always produces the same cave — this is verified by the test suite, not just claimed.

## Install

1. Copy `godot_addon/addons/fung_godot/` into your Godot 4.3+ project's `addons/` folder.
2. Enable the plugin in **Project Settings → Plugins**.
3. Set up the Python side: `pip install -r requirements.txt` (Python 3.11+) from this repo, and point the plugin at your Python executable via the `FUNG_PYTHON` environment variable, or just have `python3`/`python` on your `PATH`.

Full walkthrough: [docs/quickstart.md](docs/quickstart.md).

## Documentation

- [docs/quickstart.md](docs/quickstart.md) — install and first cave, end to end
- [docs/recipes.md](docs/recipes.md) — every built-in recipe, with its CA parameters and calibrated metric ranges
- [docs/architecture.md](docs/architecture.md) — how the editor plugin, the Python bridge subprocess, and the generation engine fit together
- [docs/bridge_protocol.md](docs/bridge_protocol.md) — the JSON request/response contract, for anyone extending the bridge
- [docs/troubleshooting.md](docs/troubleshooting.md) — common failure modes and fixes

## Repository layout

```
bridge/                Python bridge CLI: request/response JSON protocol, generation orchestration
fung_ai_v2/             Pure deterministic cellular-automata generation engine
godot_addon/addons/fung_godot/   The Godot 4 editor plugin itself
godot_addon/tests/       Headless GDScript smoke test (run in CI against a real Godot binary)
tests/                  Python test suite (pytest)
docs/                   Documentation
```

## Non-goals (v0.1)

No persistent background service, no network server, no accounts, no marketplace, no automatic art/sprite generation. The Python side runs as a short-lived subprocess per generation job, invoked non-blockingly from the editor.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the test suite and both CI checks locally, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

MIT — see [LICENSE](LICENSE).
