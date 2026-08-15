# Bridge Protocol Reference

This is the contract between the Godot addon and the Python bridge process,
as actually declared in `bridge/schemas.py` and implemented in
`bridge/fung_bridge.py` / `bridge/generation.py`. Field names and shapes
below are taken directly from those dataclasses — if you're extending the
bridge, this is the source of truth (and so are those files; re-check them
if this doc and the code ever disagree).

## Invocation

```
python -m bridge.fung_bridge --request <path/to/request.json> --response <path/to/result.json>
```

`--request` must point to an existing file. `--response` is where the
final `GenerationResult` (or an error payload of the same general shape)
is written. Exit codes: `0` success, `1` error (`BridgeError` or any other
uncaught exception), `2` cancelled.

## `GenerationRequest` (request.json)

Dataclass fields, with defaults, exactly as declared:

| Field | Type | Default |
|---|---|---|
| `protocol_version` | `int` | `1` |
| `request_id` | `str` | `""` (required — `validate()` raises if empty) |
| `generator_version` | `str` | `"0.1.0"` |
| `recipe_id` | `str` | `""` (required; must be a key in `RECIPES` — checked in `generate_candidates()`, not in `validate()`) |
| `seed` | `int` | `0` (must be `>= 0`) |
| `map_size_tiles` | `list[int]` | `[96, 96]` (must be length 2, both values `> 0`) |
| `tile_size_px` | `list[int]` | `[16, 16]` |
| `generation_budget` | `str` | `"balanced"` |
| `environment_mode` | `str` | `"manual_preset"` |
| `environment_preset` | `str` | `"limestone_cave"` |
| `overrides` | `dict[str, Any]` | `{}` |
| `candidate_count` | `int` | `24` (must be `>= 1`) |
| `job_dir` | `str` | `""` |
| `result_path` | `str` | `""` |
| `status_path` | `str` | `""` |
| `cancel_path` | `str` | `""` |

`validate()` only checks `request_id`, `recipe_id` (non-empty, not
existence in `RECIPES`), `seed >= 0`, `map_size_tiles` shape, and
`candidate_count >= 1`. A few fields are currently accepted but not yet
acted on by the generation pipeline — worth knowing if you're extending it:

- **`candidate_count` is not the actual candidate count used.** The real
  count comes from `generation_budget` via a fixed mapping in
  `generate_candidates()`: `{"fast": 3, "balanced": 6, "thorough": 12}`
  (unrecognized budget strings fall back to `6`). `candidate_count` is
  accepted and validated but otherwise unused in v0.1.
- **`environment_mode` / `environment_preset` are inert metadata.** They're
  round-tripped in the request but nothing in `generation.py` currently
  reads them to change generation behavior.
- **`overrides` is only hashed, not applied.** It's folded into
  `compute_generation_inputs_hash()` for reproducibility tracking, but the
  recipe's own `rule_string`/`initial_density`/`steps` are used as-is —
  `overrides` doesn't currently change the actual generation parameters.

## `GenerationResult` (result.json, success case)

```jsonc
{
  "request_id": "fung_123456_0",
  "success": true,
  "generator_version": "0.1.0",   // fung_ai_v2.__version__
  "recipe_id": "compact_roguelike_rooms",
  "seed": 12345,
  "candidates": [ /* Candidate[] , see below */ ],
  "warnings": [ /* str[] */ ],
  "errors": [ /* str[] */ ]
}
```

If every attempt in the request's budget fails to produce a valid
candidate, `success` is still `true`, `candidates` is `[]`, and
`warnings` contains exactly one entry:
`"No valid candidates generated (attempted <N>). Try different parameters."`
(from `generate_candidates()` in `fung_bridge.py`).

## `Candidate` (entries in `result.json`'s `candidates` array)

| Field | Type |
|---|---|
| `candidate_id` | `str` (e.g. `"candidate_001"`) |
| `seed` | `int` (the request's `seed + <index>`, per attempt) |
| `valid` | `bool` (always `true` for entries present — invalid attempts are skipped entirely rather than appearing with `valid: false`) |
| `preview_path` | `str` (relative to the job directory, e.g. `"previews/candidate_001.png"`) |
| `payload_path` | `str` (relative to the job directory, e.g. `"candidates/candidate_001.json"`) |
| `metrics` | `dict[str, float]` |
| `tags` | `list[str]` (up to 4, from `tags_from_metrics()`) |

## Candidate payload (`candidates/<candidate_id>.json`)

The full per-candidate record, written alongside the summary entry above:

```jsonc
{
  "candidate_id": "candidate_001",
  "seed": 12345,
  "grid_encoding": "rle-v1",
  "grid_size": [96, 96],           // [width, height]
  "grid": "rle-v1:...",             // see RLE format below
  "spawn_cell": [x, 0],
  "exit_cell": [x, 95],
  "markers": {
    "arena_candidates": [[x, y], ...],  // 1 cell
    "loot_candidates": [[x, y], ...],   // up to 2 cells
    "encounter_zones": []               // always empty in v0.1
  },
  "metrics": {
    "walkable_ratio": 0.0,
    "path_length": 0.0,
    "loop_count": 0.0,
    "branch_count": 0.0,
    "open_space_score": 0.0,
    "score": 0.0
  },
  "generation_inputs_hash": "sha256:..."
}
```

### Metrics

Computed in `compute_candidate_metrics()`:

- `walkable_ratio` — fraction of cells that are floor (`0`).
- `path_length` — BFS shortest-path length (4-connectivity) from
  `spawn_cell` to `exit_cell` within the spawn's connected component.
- `loop_count` — cyclomatic number of the floor-cell adjacency graph
  (`edges - nodes + 1`, floored at 0).
- `branch_count` — count of floor cells with degree >= 3 in that graph.
- `open_space_score` — the second value of `fung_ai_v2.compute_descriptors()`
  (a topology score; the first value is wall coverage, unused here).
- `score` — fraction of `fitness_targets` ranges satisfied, with partial
  credit for near-misses (`_score_from_targets()`); `0.75` flat if the
  recipe has no `fitness_targets`.

### RLE grid format (`grid_encoding: "rle-v1"`)

```
rle-v1:<count>:<value>:<count>:<value>:...
```

Values are `0` (floor) or `1` (wall). The grid is flattened **row-major**
(iterate `y` then `x`) before run-length encoding — this exactly matches
`fung_export_service.gd`'s `_decode_grid()` on the Godot side. Example: a
2x2 grid `[[0,1],[1,0]]` flattens to `[0,1,1,0]` and encodes as
`"rle-v1:1:0:2:1:1:0"`.

## `status.json` state machine

Written by `write_status()` in `fung_bridge.py`, polled every 150ms by
`fung_backend_client.gd`:

```jsonc
{
  "protocol_version": 1,
  "request_id": "fung_123456_0",
  "state": "running",     // see states below
  "progress": 0.0,         // clamped to [0.0, 1.0]
  "stage": "generating",
  "message": "",
  "updated_utc": "2026-01-01T00:00:00+00:00"
}
```

`StatusUpdate`'s dataclass default for `state` is `"queued"`, but in the
current v0.1 flow no `status.json` file exists yet during the "queued"
period (before the subprocess starts) — the first write from the bridge is
already `"running"`. Godot-side, the backend client's own `JobState` enum
(`PREPARING` -> `LAUNCHING`) represents that pre-file window.

States actually written by `fung_bridge.py`: `"running"` (stages
`"initializing"`, `"generating"`) -> one of `"completed"`, `"failed"`,
`"cancelled"`. `fung_backend_client.gd`'s poller also treats a `"error"`
state string as equivalent to `"failed"` defensively, though the current
Python code never emits `"error"` (it always emits `"failed"`).

## `BridgeError`

```jsonc
{
  "code": "RECIPE_NOT_FOUND",
  "message": "Recipe 'foo' not found",
  "details": { "recipe_id": "foo", "available": ["compact_roguelike_rooms", "..."] },
  "action": "Select a recipe from the available list"
}
```

Fields: `code` (str), `message` (str), `details` (dict), `action` (str,
a human-readable suggested next step). When a `BridgeError` is raised, it's
wrapped into an error `result.json` via `to_result_dict(request_id)`:
`{"request_id", "success": false, "error": {...}, "candidates": [], "warnings": [], "errors": [message]}`.

### Error codes that exist in the code today

- **`RECIPE_NOT_FOUND`** — raised in `generate_candidates()` when
  `request.recipe_id` isn't a key in `RECIPES`. `details` includes the
  requested `recipe_id` and the full list of `available` recipe ids.
- **`BRIDGE_ERROR`** — the catch-all in `main()`'s outer `except Exception`
  handler for anything unexpected (not a raised `BridgeError`). Built
  inline (same shape as `BridgeError.to_dict()`), with `details.type` set
  to the exception's class name. A full traceback is also written to
  `job.log` in the job directory in this case.

These are the only two codes present in the bridge as of this writing —
grep `bridge/` for `code="` / `"code":` if you're adding more and want to
keep this list current.
