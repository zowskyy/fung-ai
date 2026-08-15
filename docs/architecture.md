# Architecture

The Fung Godot Toolkit is split into a Godot-side editor plugin and a
Python-side generation engine, talking to each other through a request/
response pair of JSON files written to disk — no network socket, no
persistent daemon.

## Layers

```
fung_dock.gd (UI shell: TabContainer)
  |-- fung_generate_tab.gd   (recipe/seed/budget controls, writes request.json)
  |-- fung_candidates_tab.gd (browses result.json + previews)
  |-- fung_export_tab.gd     (TileSet/profile selection, triggers export)
  |-- "Environment" (placeholder tab, added via _add_placeholder_tab())
  |-- "Library"     (placeholder tab, added via _add_placeholder_tab())
       |
       v
fung_backend_client.gd (job lifecycle state machine, subprocess launch, status polling)
       |
       v  OS.create_process("python(3)", ["-m", "bridge.fung_bridge", "--request", ..., "--response", ...])
       |
bridge/fung_bridge.py (CLI entry point + request validation + status/result writing)
       |
       v
bridge/generation.py (orchestration: RECIPES, per-candidate generation loop, metrics, RLE encoding, preview PNGs)
       |
       v
fung_ai_v2/ (pure CA engine: CARule, step_ca, initialize_random, has_path, compute_descriptors)
```

Once a job finishes, the flow reverses on export:

```
fung_export_tab.gd -> fung_export_service.gd -> decodes result.json + candidate payload JSON
                                               -> builds a Node2D/TileMapLayer scene
                                               -> ResourceSaver.save() to a .tscn file
```

As of this writing, there is no `fung_manifest.gd` or equivalent Godot-side
manifest component — the only "manifest" code in the repo is
`bridge/manifest_writer.py`, a small Python helper (`atomic_write_json`,
`read_json`, `ensure_dir`, `sanitize_filename`) used by the bridge to write
`status.json`/`result.json`/candidate payloads atomically (write to a
`.tmp` file, then `os.replace`), not a scene-facing manifest format.

### `fung_dock.gd` — UI

Builds a `TabContainer` in code (`_ready()`), instantiates the three real
tab scripts as children, and adds two placeholder panels for "Environment"
and "Library" via `_add_placeholder_tab()`. It wires the Candidates tab's
`candidate_selected` signal to push the selection into the Export tab.

### `fung_backend_client.gd` — job lifecycle + subprocess + polling

A `Node` with a `JobState` enum (`IDLE`, `PREPARING`, `LAUNCHING`, `RUNNING`,
`IMPORTING_RESULT`, `READY_TO_EXPORT`, `EXPORTING`, `EXPORTED`, `FAILED`,
`CANCELLED`). `start_generation()` refuses to run unless the client is
`IDLE` — only one job at a time. It resolves a Python executable, launches
the bridge via `OS.create_process` (fire-and-forget: the PID is recorded
but never used to signal or kill the process), and starts a `Timer`
polling `status.json` every 150ms. State transitions (`completed` /
`failed` / `error` / `cancelled` in `status.json`) drive the corresponding
`JobState` and emit signals the Generate tab listens to.

### `bridge/fung_bridge.py` — CLI entry + validation

Invoked as `python -m bridge.fung_bridge --request <path> --response <path>`.
Reads and validates `request.json` (`GenerationRequest.from_dict()` +
`.validate()`), creates the job's `candidates/` and `previews/`
subdirectories, calls `generate_candidates()` from `generation.py`, checks
for a `cancel.request` marker file, and writes the final `result.json` plus
a last `status.json` update. Structured `BridgeError`s and any other
uncaught exception are converted into an error `result.json` (and, for
uncaught exceptions, a `job.log` with the full traceback) rather than
letting the process crash silently.

### `bridge/generation.py` — pure generation orchestration

Holds the built-in `RECIPES` dict and coordinates the `fung_ai_v2` engine:
`generate_candidate_grid()` (CA iteration + connectivity/spawn-exit check),
`compute_candidate_metrics()` (walkable_ratio, path_length, loop_count,
branch_count, open_space_score, score), `tags_from_metrics()`,
`encode_grid_rle()`, `compute_generation_inputs_hash()`, and
`render_preview_png()`. No Godot-specific or filesystem-job-layout code
lives here — `fung_bridge.py` owns the I/O side of things.

### `fung_ai_v2/` — CA engine

The underlying cellular-automaton package (`ca_engine.py`, `fitness.py`,
`validators.py`, plus `archive.py` / `exporters.py` for a MAP-Elites style
archive and a general Godot exporter). `bridge/generation.py` currently
only uses a subset of this package directly (`CARule`, `initialize_random`,
`step_ca`, `has_path`, `compute_descriptors`) — the `GridArchive`
(MAP-Elites) and `GodotExporter` pieces exist in `fung_ai_v2` but are not
part of the v0.1 bridge's generation loop, which iterates a fixed number
of independent candidates per request rather than running a QD search.

### `fung_export_service.gd` — candidate to Godot scene

Reads `result.json`, finds the requested candidate's summary entry, loads
its payload JSON (`candidates/<id>.json`), decodes the `rle-v1` grid, and
builds a `Node2D` scene with a `TileMapLayer` plus `Marker2D` nodes for
spawn/exit/gameplay markers, then saves it as a `.tscn`. See
`docs/bridge_protocol.md` for the RLE format and `docs/troubleshooting.md`
for the TileSet atlas assumptions this relies on.

## Why a subprocess-per-job model instead of a persistent server

Each Generate click creates a fresh `request_id`, a fresh job directory,
and launches a brand-new Python process that runs once and exits — there is
no long-running server process, socket, or shared in-memory state between
jobs. This matches the addon's offline-first design goals as actually
implemented:

- **No background daemon.** Nothing needs to be started, health-checked, or
  torn down alongside the editor; the plugin's `_enter_tree()`/`_exit_tree()`
  only manage the backend client and export service nodes, not a server
  process.
- **Simple failure isolation.** A crash or hang in one generation job is
  scoped to its own subprocess and job directory; it can't corrupt shared
  server state or take other jobs down with it, and `fung_bridge.py`'s
  broad exception handler ensures a `result.json` (with an error) is
  written even on an unhandled exception.
- **Job state is just files.** `status.json` and `result.json` are plain,
  atomically-written JSON, so the Godot side never needs an RPC client —
  polling a file is enough, and the job directory itself is a complete,
  inspectable record of what happened (`request.json`, `status.json`,
  `job.log` on error, `candidates/`, `previews/`).

The tradeoff, visible directly in the code, is that cancellation is only
cooperative: `cancel_generation()` writes a `cancel.request` marker file and
immediately flips the Godot-side state to `CANCELLED` (stopping the poll
timer), but the subprocess itself only checks for that marker once, after
it has already finished generating all candidates for the request — it is
never killed early. See `docs/troubleshooting.md`.

## Job directory layout

Each request gets its own directory (created by the Generate tab at
`user://.fung/jobs/<request_id>/`):

```
.fung/jobs/<request_id>/
  request.json       # GenerationRequest, written by fung_generate_tab.gd
  status.json         # StatusUpdate, written/overwritten by fung_bridge.py, polled by fung_backend_client.gd
  result.json         # GenerationResult (or an error payload), written once at the end
  job.log              # only written if an uncaught exception occurs (full traceback)
  cancel.request       # empty marker file; presence signals cooperative cancellation
  candidates/
    candidate_001.json # full per-candidate payload (grid, markers, metrics, hash)
    candidate_002.json
    ...
  previews/
    candidate_001.png  # grayscale preview (wall=black, floor=white); skipped if Pillow is unavailable
    candidate_002.png
    ...
```
