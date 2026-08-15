# Troubleshooting

## "Python executable not found" / Generate does nothing

`fung_backend_client.gd`'s `_resolve_python_executable()` tries, in order:

1. `FUNG_PYTHON` environment variable, if it's set and points to a file
   that actually exists (`FileAccess.file_exists()`).
2. `python3` on `PATH` (verified by actually running
   `python3 -c "import sys"` and checking the exit code).
3. `python` on `PATH`, same check.

If none resolve, `start_generation()` returns `false` immediately, the job
state goes to `FAILED`, and the Generate tab's status label shows "Failed
to launch generation" (the underlying error, "Python executable not
found", is emitted on the `generation_completed` signal but isn't always
what's visible at a glance in the UI).

**Fix:** set `FUNG_PYTHON` to the absolute path of the Python interpreter
that has `requirements.txt` installed (e.g. your venv's `bin/python3`),
in the environment the Godot editor process itself inherits — not just a
terminal you happen to also use.

## A recipe produces zero valid candidates

Each attempt in `generate_candidate_grid()` returns `None` (and is simply
skipped, not retried with adjusted parameters) if either:

- `has_path(grid) <= 0.0` — no connected component reaches both the top and
  bottom rows of the grid, or
- no valid spawn/exit pair can be found in that connecting component.

If **every** attempt for the request fails this way,
`generate_candidates()` in `fung_bridge.py` leaves `result.candidates`
empty and appends exactly one warning:

```
No valid candidates generated (attempted <N>). Try different parameters.
```

Note `result.success` is still `true` in this case — the bridge process
exits `0`. On the Godot side, `fung_candidates_tab.gd`'s `load_results()`
sees an empty `candidates` array and falls back to its empty state
(`"No candidates loaded"` in the metrics label); the Generate tab's status
line will read `"Generation complete, but failed to load results"`, which
can read as more alarming than it is — it just means zero candidates came
back, not that anything crashed. **The `warnings` array in `result.json`
is not currently surfaced anywhere in the addon's UI** — if you hit this,
check `result.json` directly to see the warning text.

**Fix:** try a higher generation budget (more attempts per request), a
different seed, or a larger map size — very small maps at low density are
more likely to fail the top-to-bottom connectivity check outright.

## TileSet not configured correctly for export

`fung_export_service.gd`'s `export_candidate()` first checks
`ResourceLoader.exists(tileset_path)` — if the path doesn't resolve to a
resource at all, it `push_error`s `"TileSet not found: %s"` and returns
`false` immediately, with no scene written.

If the path *does* resolve, `_build_scene()` places tiles with:

```gdscript
tilemap.set_cell(Vector2i(x, y), 0, Vector2i(is_wall, 0))
```

This hardcodes an assumption about your `TileSet` resource: it must have a
source at **atlas source id `0`**, with tiles present at **atlas
coordinates `(0, 0)`** (used for floor cells, `is_wall == 0`) and
**`(1, 0)`** (used for wall cells, `is_wall == 1`). `set_cell()` doesn't
raise an error for missing atlas coordinates — cells just render as empty/
invalid, which can look like "export succeeded but the level is blank."

**Fix:** build (or point at) a `TileSet` with a single `TileSetAtlasSource`
at id `0`, containing at minimum two tiles side by side at atlas
coordinates `(0, 0)` and `(1, 0)`.

One related thing worth knowing about the current Export tab:

- The **profile selector** (Top-Down / Platformer / Debug Visualization)
  and the four **layer toggle checkboxes** (Terrain, Collision, Navigation,
  Preview) are UI state only — `_build_scene()` ignores the `export_profile`
  parameter it's handed and always builds the same Terrain `TileMapLayer` +
  spawn/exit/gameplay markers, regardless of profile or toggle state.

## Generation seems stuck in "Running"

Cancellation is cooperative and asymmetric between the two sides:

- Clicking **Cancel** (`fung_backend_client.gd`'s `cancel_generation()`)
  writes an empty `cancel.request` marker file into the job directory,
  immediately sets the Godot-side job state to `CANCELLED`, and stops the
  status-polling timer. From the UI's perspective, this happens right
  away.
- The Python subprocess, however, is never signaled or killed — `main()`
  in `fung_bridge.py` only checks whether `cancel.request` exists **once**,
  after `generate_candidates()` has already finished generating every
  candidate for the request. If it exists at that point, the bridge writes
  a `"cancelled"` status and a `success: false` result — but by then Godot
  has already stopped polling, so it never observes that final state.

In practice: the UI reports "Cancelled" quickly, but the underlying Python
process keeps running in the background until it finishes its full
attempt budget on its own (a `"thorough"` budget on a large map can take a
while, since progress inside `generate_candidate_grid()`'s CA loop is
only reported every 10 steps).

There is currently **no way to force-kill the subprocess from the UI**, and
no manual "reset" control if the backend client's state ever gets stuck
somewhere other than `IDLE` — `_reset_for_next_job()` only runs when the
poller observes a terminal `status.json` state. If a job genuinely wedges
(e.g. the subprocess itself hangs and never writes a terminal status),
disabling and re-enabling the plugin in **Project Settings > Plugins** is
the practical way to get a fresh `FungBackendClient` back to `IDLE`.

## Only one job runs at a time

`start_generation()` refuses to launch (and `push_error`s) unless the
backend client is `IDLE`. If you click **Generate** while a previous job
hasn't reached a terminal state yet, the Generate tab's status label shows
"Backend not ready" and nothing is launched — this isn't a bug, but it can
look like a missed click if the previous job is still finishing up.
