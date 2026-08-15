# Quickstart

This walks through installing the Fung Godot Toolkit addon into a Godot 4
project, setting up the Python side of the bridge, and generating your first
cave level.

## 1. Requirements

- Godot **4.3+** (the addon's CI validates against Godot `4.3.0` headless).
- Python **3.11+** (matches the version CI installs; `pyproject.toml`
  declares a `>=3.10` floor, but use 3.11 to match what's actually tested).
- The Python dependencies in `requirements.txt` at the repo root: `numpy`,
  `scipy`, `httpx`, `jsonschema`, `Pillow`.

## 2. Install the addon into your Godot project

Copy the addon folder into your project's `addons/` directory so the layout
looks like:

```
your_project/
  addons/
    fung_godot/
      plugin.cfg
      fung_editor_plugin.gd
      services/
      ui/
```

The source lives at `godot_addon/addons/fung_godot/` in this repo — copy
that whole directory in as `addons/fung_godot/`.

Then in Godot: **Project > Project Settings > Plugins**, find "Fung Godot
Toolkit" (per `plugin.cfg`, version `0.1.0`), and enable it. This runs
`fung_editor_plugin.gd`, which creates the backend client and export
service and docks the Fung panel (`DOCK_SLOT_LEFT_BR`).

## 3. Set up the Python environment

From the repo root (or wherever you keep the bridge's Python code —
`bridge/` and `fung_ai_v2/` need to be importable as packages, so run
things from a directory that contains both):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Point the plugin at the right Python executable

The backend client (`fung_backend_client.gd`, `_resolve_python_executable()`)
resolves the interpreter in this order:

1. The `FUNG_PYTHON` environment variable, if it's set **and** points to a
   file that exists.
2. `python3` on `PATH`, verified by running `python3 -c "import sys"`
   and checking for a zero exit code.
3. `python` on `PATH`, same check.

If none of these resolve, `start_generation()` fails immediately and the
Generate tab reports "Failed to launch generation."

If your bridge dependencies live in a virtualenv, set `FUNG_PYTHON` to the
absolute path of that venv's `python`/`python3` binary before launching the
Godot editor (e.g. export it in your shell profile, or launch the editor
from a shell where it's already set).

## 5. Generate your first cave

1. Open the **Fung** dock (bottom-right dock area by default).
2. **Generate tab**: pick a recipe from the dropdown (`compact_roguelike_rooms`,
   `open_exploration`, or `dense_maze` as of v0.1 — see `docs/recipes.md`
   for the current list). Set map width/height (default 96x96, range 8-512)
   and a seed (default 0; use "Randomize" for a random one). Pick a budget —
   Fast (3 candidates), Balanced (6, the default), or Thorough (12).
3. Click **Generate**. This launches
   `python -m bridge.fung_bridge --request <job_dir>/request.json --response <job_dir>/result.json`
   as a subprocess and polls `<job_dir>/status.json` every 150ms for
   progress. The job directory is `user://.fung/jobs/<request_id>/` (Godot's
   per-project editor data directory, not `res://` — it isn't part of your
   version-controlled project tree).
4. When generation completes, results are loaded automatically into the
   **Candidates tab**. Browse the list (each entry shows generated tags),
   and select one to see its preview PNG and metrics (walkable ratio, path
   length, loop count, branch count, open space score).
5. **Export tab**: with a candidate selected, enter the path to a `TileSet`
   resource (`res://path/to/tileset.tres`) and click **Export**.

## 6. What you get

The export service (`fung_export_service.gd`) writes a scene containing a
`TileMapLayer` ("Terrain"), a `PlayerSpawn` marker, an `Exit` marker, and a
`GameplayMarkers` group with arena/loot candidate markers, to:

```
user://generated/fung/levels/<candidate_id>.tscn
```

Note this is a fixed path built from `_export_root` ("user://generated/fung/")
plus `levels/<candidate_id>.tscn" — the Export tab's "Scene name" and
"Export folder" text fields are not currently wired to the actual save
location (see `docs/troubleshooting.md`). Because it's under `user://`, the
exported scene lives in the editor's per-project user data directory, not
under your project's `res://` tree — copy or move it into your project if
you want it version-controlled.

The `TileMapLayer` expects a `TileSet` with a source at atlas source id `0`
providing tiles at atlas coordinates `(0, 0)` (floor) and `(1, 0)` (wall) —
see `docs/troubleshooting.md` for details on setting this up correctly.
