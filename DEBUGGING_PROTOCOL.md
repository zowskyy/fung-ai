# Debugging & Auditing Protocol (research-informed, 2026)

A strict, repeatable loop for diagnosing defects in this project. Derived from:
- Hopman (2026), *Diagnose a bug: build the feedback loop first* — scientific-method debugging; the loop is phase 1 and carries the work.
- `systematic-debug` skill (gist) — Reproduce → Isolate → Hypothesize (ranked, falsifiable) → Stress-test → Fix + regression test.
- PyInstaller docs (common-issues, advanced-topics, CHANGES 6.9+) — frozen-app spawn semantics, `--onefile` two-process bootloader, `PYINSTALLER_RESET_ENVIRONMENT`, `multiprocessing.freeze_support()`.
- FSE 2026 *Grounded Theory of Debugging* — alternate static navigation and dynamic execution; forward/backward tracing; build a mental model.
- CloudThinker incident framework — timeline-first, change-first heuristic, bisect by layer.

## The loop (do not skip steps; do not theorize before step 1)

### 0. Open an audit timeline
Write a timestamped log of every action + observation (`steps taken / what I saw / what I concluded`).
Never reconstruct from memory. Stop re-checking the same thing twice.

### 1. Build the feedback loop (BEFORE any theory)
Produce ONE command that goes **red** on the bug and **green** when fixed. Criteria:
- **Red-capable**: runs the real code path, asserts the exact symptom.
- **Deterministic**: same verdict every run.
- **Fast**: seconds, not minutes.
- **Unattended**: no human in the loop.
For spawn/race bugs this is a harness that launches N copies and asserts the steady-state process count.
> Rule: stop and return here if you read code for a theory before this loop exists.

### 2. Reproduce & minimise
Run the loop. If it doesn't reproduce, say so and stop. Shrink to the minimal trigger.

### 3. Enumerate the mechanism completely (don't stop at the first path)
For "process spawns itself / many windows" bugs, grep the WHOLE codebase for EVERY spawn primitive:
`subprocess`, `Popen`, `sys.executable`, `multiprocessing`, `ProcessPool`, `QProcess`,
`os.exec*`, `os.spawn*`, `concurrent.futures`, `QThread`->process, `PYINSTALLER_RESET_ENVIRONMENT`.
Then check PyInstaller frozen semantics (bootloader = extra process; `--onefile` re-extracts on each `sys.executable` relaunch).

### 4. Hypothesize (ranked, falsifiable)
Write 3–5 causes, each with a **prediction** that can disprove it.
> Rule: a cause you cannot falsify is not a hypothesis.

### 5. Instrument & stress-test (one variable per probe)
Amplify flaky/race bugs: tight loops, many concurrent launches, reduced timeouts, run 100×.
Raise the reproduction rate (more concurrent launches, tighter stagger, add load) until the bug fails in **>5% of runs** — at that point the loop is trustworthy/red-capable (we don't need to force it to 50%; we just need it observable, not a once-in-a-million fluke). Rerun the harness after EVERY fix attempt.

### 6. Fix (smallest change) + regression test
Smallest possible change. Keep the loop as a committed regression test so it cannot recur.
Remove temporary probes. Run the existing suite.

### 7. Verify & close
Loop is green across many runs. Update the timeline with root cause + fix.

## Known frozen-app spawn traps (checklist for this project)
- [ ] No `sys.executable` used to relaunch when `getattr(sys,'frozen',False)` is True (use `shutil.which` + non-frozen fallback).
- [ ] No `multiprocessing` without `multiprocessing.freeze_support()` at entry.
- [ ] App restart via `sys.executable` sets `PYINSTALLER_RESET_ENVIRONMENT=1` (PyInstaller ≥6.9).
- [ ] Single-instance guard runs BEFORE heavy imports and BEFORE the long `--onefile` extraction window.
- [ ] Prefer `--onedir` over `--onefile` for shipped GUI apps (no 3–10s extraction burst that invites double-click races).
- [ ] Remember: `--onefile` shows TWO processes at rest (bootloader + app); `--onedir` on Windows shows ONE.
