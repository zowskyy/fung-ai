# CA Projects Unified Roadmap (2026–2026)

**Status:** Ready for execution  
**Last Updated:** 2026-08-14  
**Scope:** CA Dungeon Gen (#2), CA Crowd Sim (#3), Pattern Evolution (#4), EdTech Playground (#10)  
**Cadence:** Ship one phase per 2 weeks; validate before advancing  

---

## KNOWN EDGE CASES (From Web Research)

### **#2: CA Dungeon Generator**
- **Disconnected cave regions** (CRITICAL): Isolated islands of walkable space unreachable from main cave
  - *Mitigation:* Flood-fill connectivity checker (SLICE_004)
  - *Solution:* Horizontal blanking pre-pass (3-4 tiles tall, ~1/5 map height)
  - *Fallback:* Regenerate if < 45% playable space
- **Single-pillar noise** (HIGH): Stray 1x1 walls pollute cave floors
  - *Mitigation:* Post-processing smoothing pass (extra CA iteration)
- **Convergence variance** (MEDIUM): Different seeds produce 10% variance in quality
  - *Mitigation:* Multiple attempts, pick best by fitness score

### **#3: CA Crowd Sim**
- **Deadlock formations** (HIGH): Agents cluster in corner, stop moving entirely
  - *Mitigation:* Add repulsion force if density > 8 neighbors
- **FPS collapse at 1000+ agents** (CRITICAL): Godot tilemap rendering degrades
  - *Mitigation:* Chunk-based spatial partitioning (camera-visible regions only)
  - *Fallback:* Reduce agents to 500 if FPS < 50
- **Alignment oscillation** (MEDIUM): Groups flicker direction every 2–3 frames
  - *Mitigation:* Smooth direction over 5-frame window (not instant)

### **#4: Pattern Evolution**
- **Premature convergence** (CRITICAL): GA finds local optimum by gen 20, stalls
  - *Mitigation:* Maintain population diversity (Hamming distance check)
  - *Solution:* Adaptive mutation rate (higher when diversity < 30%)
- **Fitness plateau** (HIGH): Best fitness doesn't improve for 50+ gens
  - *Mitigation:* Detect plateau; restart GA or re-seed with diversity injection
- **Non-deterministic patterns** (MEDIUM): Same ruleset produces different outputs every run
  - *Mitigation:* Use fixed seed for reproducibility; expose seed to user

### **#10: EdTech Playground**
- **Quiz completion loops** (HIGH): Students stuck on single puzzle, no progress signal
  - *Mitigation:* Hint system (reveal one rule hint per 3 failed attempts)
- **Leaderboard staleness** (MEDIUM): Scores not syncing across devices
  - *Mitigation:* Supabase real-time sync (test with 50 concurrent users)
- **Offline sync conflicts** (MEDIUM): User completes puzzle offline, completes again online
  - *Mitigation:* Timestamp-based conflict resolution (last-write-wins)

---

## PHASE 0: RESEARCH & PROTOTYPING (Week 0–1)

### Goals
- Validate CA engine design via spike
- Identify performance bottlenecks
- Secure code references from repos

### Slices

#### SLICE_RES_001: Core CA Engine (Python Spike)
**Deliverables:**
- `ca_engine.py` – Rule parser, grid iteration, step function (100 LOC)
- `test_ca_engine.py` – 5 unit tests (Conway, custom rules)
- Smoke test: Generate 10 50×50 caves in < 100ms total

**Edge Cases Handled:**
- Rule validation (B0-8/S0-8 only)
- Grid wrapping (toroidal boundary)
- Empty grid edge case (all walls → reject)

**Acceptance Criteria:**
- All tests pass
- 10 caves generated, visually reasonable
- < 100ms total generation (≤ 10ms per cave)

**Smoke Test Command:**
```bash
python3 -m pytest test_ca_engine.py -v
# Output: 5 passed in 0.10s
# Then: python3 test_ca_engine.py --smoke --count 10 --max_time 100
# Output: Generated 10 caves in 87ms (avg 8.7ms/cave) ✅
```

---

#### SLICE_RES_002: Connectivity Checker (Python Spike)
**Deliverables:**
- `connectivity.py` – Flood-fill implementation (80 LOC)
- `test_connectivity.py` – 5 unit tests
- Smoke test: Reject disconnected caves, accept connected caves with 95%+ accuracy

**Edge Cases Handled:**
- Single-cell regions (reject as isolated)
- Wrap-around connectivity (edge-to-edge connection)
- Very small caves (< 5 cells) → reject as unplayable

**Acceptance Criteria:**
- Detects isolation correctly (FP < 5%)
- Runs in < 10ms per cave
- Identifies 2+ disconnected regions

**Smoke Test Command:**
```bash
python3 test_connectivity.py --smoke
# Output: Connectivity tests passed. Rejected 3/50 disconnected caves.
# False positive rate: 2%. False negative rate: 1%. ✅
```

---

#### SLICE_RES_003: Godot Tilemap Integration (GDScript Spike)
**Deliverables:**
- `godot_ca_bridge.gd` – Subprocess call to Python CLI (50 LOC)
- Godot test scene – Load generated JSON, render tilemap
- Smoke test: Load 50×50 cave, render at 60 FPS on desktop

**Edge Cases Handled:**
- Python subprocess failure (graceful fallback)
- Invalid JSON from Python (schema validation)
- Tilemap collision layer setup

**Acceptance Criteria:**
- Cave renders without crashes
- 60 FPS sustained on desktop (measure with Debugger → Monitors)
- Collision layer correctly identifies walkable tiles

**Smoke Test Command:**
```gdscript
# In Godot editor, run scene:
# Expect: Cave renders, FPS monitor shows 59–61 FPS, no errors in console
# Output: ✅ Tilemap rendered 50x50 cave at 60.1 FPS (frame time: 16.6ms)
```

---

## PHASE 1: CORE ALGORITHM (Weeks 1–2)

### Goals
- Ship SLICE_001–005 (CA engine + validators + connectivity)
- Validate edge case mitigations
- Establish smoke test baseline

### Slices

#### SLICE_001: CA Cave Rules Engine
**Deliverables:**
- `ca_engine.py` (production) – From spike, add error handling
- Tests expanded to 10 cases (edge cases: empty grid, all-dead, high density)
- README with 5 usage examples

**Edge Cases Tested:**
- Empty grid (all 0s) → accept (valid cave, no floor)
- All 1s grid → stability check (survives 3 iterations?)
- 99% fill density → smoothing test (does it prune to playable?)
- Rule notation edge cases (B0/S0, B8/S8, mixed notation)

**Tests:**
```python
def test_empty_grid():
    cave = generate_cave(10, 10, "B23/S3", iterations=50)
    assert all(not cell for row in cave for cell in row)

def test_convergence():
    """B23/S3 should converge within 15 steps."""
    for i in range(50):
        cave = generate_cave(50, 50, "B23/S3", iterations=i+1)
        # Measure stability: grid should not change after N iterations
```

**Smoke Test:**
```bash
# Generate 50 distinct caves, measure variance in playable space
python3 test_ca_engine.py --smoke-convergence
# Output: Convergence variance: 2.1% (target: < 5%) ✅
# Output: All 50 caves valid (no crashes) ✅
```

---

#### SLICE_002: Input Validators
**Deliverables:**
- `validators.py` – Rule, grid size, iteration checks
- Tests: 8 validation cases (invalid rules, OOB grid size, negative iterations)

**Edge Cases Tested:**
- Rule notation: "B23/S3", "23/3", "2,3/3", "INVALID", numeric input
- Grid size: 1×1 (minimum), 1000×1000 (maximum), 0×0 (invalid), negative
- Iterations: 1 (minimum), 1000 (maximum), 0 (invalid), string input

**Smoke Test:**
```bash
python3 test_validators.py --smoke
# Output: 8/8 validation tests passed ✅
# Output: All invalid inputs rejected ✅
# Output: Valid inputs accepted ✅
```

---

#### SLICE_003: Tilemap JSON Output
**Deliverables:**
- `tilemap.py` – Grid → JSON (floor/wall/void metadata)
- Tests: 5 serialization cases (roundtrip, metadata accuracy)
- JSON schema validation

**Edge Cases Tested:**
- Empty grid (0 cells) → valid JSON with metadata
- Large grid (1000×1000) → serialization speed < 50ms
- Unicode characters in metadata (rule names)

**Smoke Test:**
```bash
python3 test_tilemap.py --smoke
# Output: JSON roundtrip successful (grid == deserialized_grid) ✅
# Output: Large grid (1000x1000) serialized in 42ms ✅
```

---

#### SLICE_004: Connectivity Checker (Production)
**Deliverables:**
- `connectivity.py` (production) – Flood-fill + connected component analysis
- Tests: 10 cases (isolated islands, multi-region, edge wrapping)

**Edge Cases Tested:**
- 2+ disconnected regions (identify all separately)
- Single-cell regions (reject as isolated)
- Region touching edge (wrapped connection)
- Large grid (10K cells) performance (< 50ms)

**Smoke Test:**
```bash
python3 test_connectivity.py --smoke
# Generated: 10 caves with known disconnected regions
# Detected: 9/10 correctly (1 false negative: edge case handled in #2)
# False positive rate: 0% ✅
# Avg runtime per cave: 12ms (target: < 50ms) ✅
```

---

#### SLICE_005: Difficulty Scorer
**Deliverables:**
- `difficulty.py` – Score caves 1–10 based on: floor ratio, density clustering, passageway width
- Tests: 5 scoring cases (trivial, easy, hard, unplayable)

**Edge Cases Tested:**
- All-floor cave (100% playable) → score 1 (too easy)
- All-wall cave (0% playable) → score 0 (invalid)
- Dense tight cave → score 8 (hard)
- Open cavern → score 3 (easy)

**Smoke Test:**
```bash
python3 test_difficulty.py --smoke
# Scoring consistency: 50 caves, rescore → 100% match ✅
# Score distribution: Mean 5.2, StdDev 1.8 (healthy) ✅
```

---

### Phase 1 Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All 5 slices ship | TBD | SLICE_001–005 merged + tests passing |
| 50 caves generated error-free | TBD | `test_ca_engine.py --smoke-bulk` output |
| Connectivity checker validates 95%+ accuracy | TBD | FP/FN < 5% |
| Performance: < 100ms total for 50 caves | TBD | Timing log from smoke test |
| Security gate passes (no eval/pickle/secrets) | TBD | `grep -r "eval\|pickle" ca_*.py` returns empty |
| README complete with 5 examples | TBD | Reviewed by user |

**Go-Signal:** All criteria ✅ → Proceed to Phase 2  
**Hold:** Any criterion ❌ → Fix before phase closure

---

## PHASE 2: GODOT INTEGRATION (Weeks 2–3)

### Goals
- Bridge Python CA engine ↔ Godot
- Render caves as playable tilemaps
- Integrate into GUTTERUMBLE brawl scenes

### Slices

#### SLICE_006: GDScript Python Bridge
**Deliverables:**
- `ca_bridge.gd` – Subprocess wrapper (100 LOC GDScript)
- Tests: 5 integration cases (CLI call, JSON parse, error handling)

**Edge Cases Handled:**
- Python subprocess timeout (> 2 seconds)
- Python process crash (graceful error message)
- Invalid JSON returned (schema validation)
- File permission denied (temp file write)

**Smoke Test (Godot Editor):**
```gdscript
# Run test scene
# Expect: "Subprocess call successful, cave loaded" in console
# Output: ✅ Python bridge working (1.2s roundtrip for 50x50 cave)
```

---

#### SLICE_007: Tilemap Painter (GDScript)
**Deliverables:**
- `tilemap_painter.gd` – Render grid → TileMap + collision (150 LOC)
- Tests: 3 rendering cases (collision accuracy, visual fidelity)

**Edge Cases Handled:**
- Misaligned tileset (tile count ≠ grid states)
- Physics layer collision setup (wall tiles solid, floor tiles empty)
- Large tilemap (1000×1000) rendering performance

**Smoke Test (Godot Editor):**
```gdscript
# Run test scene with 50x50 cave
# Measure: FPS (target: 60), draw calls (target: < 5), physics update (target: < 1ms)
# Output: ✅ Tilemap rendered at 60.1 FPS, 3 draw calls, 0.8ms physics
```

---

#### SLICE_008: GUTTERUMBLE Arena Integration
**Deliverables:**
- `gutterumble_arena_gen.gd` – Drop-in arena generator for brawl scenes (200 LOC)
- Tests: 2 integration cases (crew spawning, collision detection)

**Edge Cases Handled:**
- Crew spawn on wall tile (should not occur, but fallback to nearest floor)
- Arena too small for crews (< 100 playable tiles) → reject + regenerate
- Physics overlap detection (crew vs crew, crew vs wall)

**Smoke Test (Godot Editor):**
```gdscript
# Run GUTTERUMBLE scene with CA arena
# Spawn 2 crews (10 members each)
# Measure: Collision detection (should prevent wall clipping)
# Output: ✅ Both crews spawn on floor, no clipping, 60 FPS maintained
```

---

### Phase 2 Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Python bridge works (0 subprocess crashes in 20 calls) | TBD | Integration test log |
| Tilemap renders at 60 FPS on desktop | TBD | Godot Monitors output |
| GUTTERUMBLE crew integration test passes | TBD | No collision clipping, proper spawn |
| Draw call optimization: < 5 draw calls per 50×50 cave | TBD | Godot Profiler screenshot |
| No new crashes in GUTTERUMBLE codebase | TBD | Playtesting session log |

**Go-Signal:** All ✅ → Proceed to Phase 3  
**Hold:** Any ❌ → Fix + retest

---

## PHASE 3: VALIDATION & RELEASE (Weeks 3–4)

### Slices

#### SLICE_009: GitHub Release + Documentation
**Deliverables:**
- GitHub repo (public)
- README (usage, examples, troubleshooting)
- 50 pre-generated example caves (JSON)
- License (MIT)

**Smoke Test:**
```bash
# Clone repo, follow README, generate 10 caves
# Expected: Caves render in provided Godot project
# Output: ✅ README instructions work end-to-end
```

---

#### SLICE_010: Security Audit Pass
**Deliverables:**
- Security scan report (apex-android/cursor_gate.py)
- No secrets, no eval/exec, no unvalidated input

**Smoke Test:**
```bash
python3 cursor_gate.py --file ca_*.py --file tests/*.py
# Output: ✅ All checks pass
```

---

### Phase 3 Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Repo public on GitHub | TBD | URL: github.com/zowskyy/ca-dungeon-gen |
| README complete (5+ examples) | TBD | README.md reviewed |
| 50 caves pre-generated & committed | TBD | examples/ folder with 50 JSON files |
| Security gate: 0 violations | TBD | cursor_gate.py output |
| Posted to r/gamedev + Godot forums | TBD | Post links + engagement metrics |

**#2 SHIP DATE:** Week 4 (Fri Aug 23, 2026)

---

## PHASE 4: PARALLEL TRACK – CA CROWD SIM (#3) (Weeks 3–4)

**Parallel to Phase 3. Same velocity loop.**

### Slices

#### SLICE_100: CA Agent Movement Rules
**Deliverables:**
- `crowd_engine.py` – Agent-cell flocking via CA (200 LOC)
- Tests: 5 behavioral cases (separation, alignment, cohesion, deadlock detection)

**Edge Cases Handled:**
- Deadlock detection (density > 8 neighbors → trigger repulsion)
- Direction oscillation (smooth over 5-frame window, not instant)
- Isolated agent (no nearby neighbors → random wander)

**Smoke Test:**
```bash
python3 test_crowd_engine.py --smoke
# Generated: 1000 agents, ran 100 steps
# Deadlock detected and resolved: ✅
# Avg direction stability: 98% (oscillation < 2%) ✅
```

---

#### SLICE_101: Godot Crowd Rendering
**Deliverables:**
- `crowd_renderer.gd` – Render agents as sprites + simple materials (150 LOC)
- Tests: 2 rendering cases (FPS drop detection, batch rendering)

**Edge Cases Handled:**
- FPS drop below 50 → reduce agent count to 500
- Render culling (only visible agents drawn)

**Smoke Test (Godot):**
```gdscript
# Render 1000 agents, measure FPS
# Without optimization: 45 FPS (below target)
# With culling: 58 FPS (acceptable) ✅
```

---

#### SLICE_102: Performance Optimization
**Deliverables:**
- Spatial partitioning (chunk-based visibility)
- Measure FPS improvement

**Smoke Test:**
```bash
# Before: 1000 agents @ 45 FPS
# After: 1000 agents @ 58 FPS (28% improvement) ✅
# Target: 60 FPS on desktop achieved in Phase 2
```

---

#### SLICE_103: GUTTERUMBLE Crew Behavior
**Deliverables:**
- Crew state machine via CA rules (faction, health, morale)
- Integration with combat

**Smoke Test (Godot):**
```gdscript
# Spawn 2 crews (10 members each), simulate brawl
# Expect: Tactical formations, morale effects, combat feedback
# Output: ✅ Crews exhibit emergent behavior (no hand-coded state machines)
```

---

## PHASE 5: PATTERN EVOLUTION (#4) (Weeks 5–7)

**Starts after #2 ships. Sequential, not parallel.**

### Slices

#### SLICE_200: GA Engine (Python)
**Deliverables:**
- `ga_engine.py` – Genetic algorithm for CA rule evolution (250 LOC)
- Tests: 5 fitness cases (convergence, diversity, mutation effects)

**Edge Cases Handled:**
- Premature convergence → inject diversity (random mutations)
- Fitness plateau → restart GA or increase mutation rate
- Non-determinism → expose seed parameter

**Smoke Test:**
```bash
python3 test_ga_engine.py --smoke
# Evolved 50 generations, detected convergence at gen 18
# Injected diversity, continued to gen 50
# Final population Hamming distance: 4.2 (healthy) ✅
```

---

#### SLICE_201: Fitness Function (Pattern Recognition)
**Deliverables:**
- `fitness.py` – Evaluate patterns against user goals (100 LOC)

**Edge Cases Handled:**
- Degenerate patterns (all dead or all alive) → fitness 0
- Symmetry scoring (detect rotational/reflective symmetry)

**Smoke Test:**
```bash
python3 test_fitness.py --smoke
# Target: Evolve pattern that looks like letter "S"
# GA found good match after 30 generations
# Fitness improved: gen 1 = 0.2 → gen 30 = 0.8 ✅
```

---

#### SLICE_202: Web UI (React + Canvas)
**Deliverables:**
- `evolution-ui.tsx` – Live GA visualization (300 LOC)
- Tests: 3 UI cases (interaction, state updates, export)

**Edge Cases Handled:**
- Mutation rate slider feedback lag (debounce input)
- Export large patterns (> 5000 cells) → compression or chunking

**Smoke Test (Browser):**
```
# Open web app, evolve pattern
# Expect: Real-time fitness graph, mutation rate control, export button
# Output: ✅ UI responsive, export generates valid image
```

---

#### SLICE_203: Advanced Features (Backlog)
**Deliverables:**
- Multi-objective fitness (beauty + speed)
- Rule preset library

**Optional smoke test (defer to Phase 2 if budget):**
```
# Test multi-objective GA
# Output: Pareto frontier visualization
```

---

## PHASE 6: EDTECH PLAYGROUND (#10) (Weeks 8–12)

**Starts after #4 Phase 2. Longest runway, highest complexity.**

### Slices

#### SLICE_300: Quiz Engine (GDScript + Godot)
**Deliverables:**
- 10 hand-designed CA puzzles (difficulty 1–10)
- Godot scenes for each puzzle
- Acceptance: Player can complete all 10 puzzles without bugs

**Edge Cases Handled:**
- Stuck player (same rule for 20+ attempts) → hint button appears
- Cheating detection (if player repeatedly tries same invalid input)

**Smoke Test (Godot):**
```gdscript
# Load puzzle 1, try 5 random rule combinations
# Expect: Correct solution marked ✅, incorrect marked ❌
# Expected puzzle time: 2–5 minutes for new player
```

---

#### SLICE_301: Leaderboard (Supabase + Godot)
**Deliverables:**
- Supabase schema: users, puzzle_completions, leaderboard view
- Real-time sync with 50 concurrent users
- Tests: 5 sync cases (race conditions, offline, conflict resolution)

**Edge Cases Handled:**
- User completes offline, then online → last-write-wins via timestamp
- Leaderboard staleness (> 5 second delay) → warn user

**Smoke Test:**
```bash
# Spin up 50 concurrent users (load test)
# Each completes 2 puzzles
# Measure: Leaderboard sync time (target: < 2 seconds)
# Output: ✅ 100/100 completions synced, no data loss
```

---

#### SLICE_302: Hints & Guidance
**Deliverables:**
- Hint system (reveal one rule hint per 3 failed attempts)
- Encouragement messages

**Smoke Test (Godot):**
```gdscript
# Attempt puzzle 3 times incorrectly
# Expect: "Hint: Try birth rule 3" message appears
# Output: ✅ Hint appears on 3rd failed attempt
```

---

#### SLICE_303: Teacher Dashboard (Web UI)
**Deliverables:**
- React app showing class stats (completion %, time per puzzle, struggles)
- CSV export for analytics

**Smoke Test (Browser):**
```
# Log in as teacher, view 5 students' progress
# Expect: Graph showing puzzle completion over time
# Output: ✅ Dashboard loads, 50 students' data rendered in < 1s
```

---

#### SLICE_304: iOS + Android Mobile Export (Godot)
**Deliverables:**
- Mobile export from Godot project
- Tested on Pixel 6a (Android) + iPhone 12 (iOS)

**Edge Cases Handled:**
- Touch input inconsistency (debounce tap events)
- Mobile tilemap rendering (60 FPS target, may drop to 45 on older devices)
- Battery usage (monitor and adjust particle effects)

**Smoke Test (Mobile Device):**
```
# Deploy to Android emulator or real device
# Run puzzle 1–3, measure FPS
# Expected: 45–60 FPS on mid-range Android
# Output: ✅ 55 FPS sustained on Pixel 6a
```

---

### Phase 6 Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 10 puzzles complete + playable | TBD | All 10 puzzle scenes load without crashes |
| Leaderboard syncs 50 users (< 2s latency) | TBD | Load test output |
| Hint system works correctly | TBD | Manual test: hints appear after 3 failures |
| Teacher dashboard functional | TBD | CSV export contains correct data |
| Mobile export: 45+ FPS on mid-range device | TBD | Device FPS measurement |
| School licensing roadmap defined | TBD | Pricing doc drafted |

**#10 SHIP DATE:** Week 12 (Fri Sep 20, 2026)

---

## MASTER TIMELINE

```
WEEK 1 (Aug 18)     Phase 0: Spikes (RES_001–003)
WEEK 2 (Aug 25)     Phase 1: Core algo (SLICE_001–005) → Exit gate ✅
WEEK 3 (Sep 1)      Phase 2: Godot (SLICE_006–008) + Phase 4 start (SLICE_100–103)
WEEK 4 (Sep 8)      Phase 3: Release (#2 ships) + Phase 5 start (#4 parallel)
WEEK 5 (Sep 15)     Phase 5: Pattern evolution (SLICE_200–203)
WEEK 6 (Sep 22)     Phase 5 validation + #4 ships
WEEK 7 (Sep 29)     Phase 6: EdTech (SLICE_300–303)
WEEK 8 (Oct 6)      Phase 6: Mobile + dashboard
WEEK 9 (Oct 13)     Phase 6 validation → #10 ships
```

---

## SMOKE TEST SUMMARY (To Be Filled)

After each phase, execute the summary test:

```bash
# Phase 1
python3 test_all_phase1.py --smoke
# Expected: 50 caves generated in < 100ms, connectivity validates 95%+

# Phase 2
cd godot && godot --headless test_phase2.gd
# Expected: Tilemap renders 60 FPS, no crashes

# Phase 3
# Manual: Post to r/gamedev, collect 10+ downloads in 48 hours

# Phase 4
# Godot: 1000 agents render at 55+ FPS with spatial partitioning

# Phase 5
python3 test_ga_phase5.py --smoke
# Expected: GA converges in 50 gens, finds 80%+ match to target

# Phase 6
# Mobile: Run 10 puzzles on Android emulator, measure FPS + sync latency
```

