# CODE SALVAGE INVENTORY – CA Projects (#2, #3, #4, #10)

**Last Updated:** 2026-08-14  
**Scope:** Identify reusable code from 10 repos → direct slices for CA Dungeon Gen, CA Crowd Sim, Pattern Evolution, EdTech Playground.

---

## TIER-1: IMMEDIATE REUSE (Ship in Slice 001–010)

### 🔥 **repurpose-engine** (226 LOC Python)
**Status:** Production-ready, tested, shipped.  
**Relevance:** Content generation logic (cleaning, truncation, platform formatting).

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `clean_transcript()` | Clean CA rule generation input (user-provided rules as text) | #2 SLICE_001 | Adapt to strip invalid CA syntax before parsing rule numbers (0–255) |
| `is_valid_content()` | Validate cave tilemap JSON before shipment | #2 SLICE_009 | Reuse logic: reject empty/junk before commit |
| `truncate_to_limit()` | Cap generated CA description text (for UI labels) | #4 SLICE_001 | Already handles edge cases (space-free runs) |
| `PLATFORM_LIMITS` dict | Bound output sizes (e.g., UI tweet-length descriptions) | #4, #10 | Direct dict reuse |

**Why:** Already handles Unicode, emoji, punctuation edge cases. Tests passed. Zero modifications needed.

**Ship plan:**
```python
# repurpose-engine/repurpose.py → ca-dungeon-gen/validators.py
# Copy: clean_transcript(), is_valid_content(), truncate_to_limit()
# Tests: adapt test_repurpose.py for CA input validation
```

---

### **pettu** (React + TypeScript, ~200 LOC in stores)
**Status:** Shipped mobile companion app. Zustand state management.  
**Relevance:** Companion AI state mgmt, dialogue loops, async error handling.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `useCompanionStore` (Zustand) | Base architecture for #10 (EdTech quest state, user progress, leaderboard) | #10 SLICE_006 | `questState`, `pendingAction`, `error` mirror `companionStore` structure |
| `pendingAction` pattern | Track user interaction state during CA evolution (#4 SLICE_003) | #4 SLICE_003 | "Evolving..." button state, prevents double-clicks |
| Error message pattern | Display CA rule validation errors in web UI | #4, #10 UI | Reuse `careError` → `caError` pattern |

**Why:** Zustand is lightweight, performant, already battle-tested in production app. No external backend required for local state.

**Ship plan:**
```typescript
// pettu/src/stores/companionStore.ts → pattern-evolution/stores/evolutionStore.ts
// Adapt: CompanionUiState → EvolutionState (rules, patterns, evolution status)
// Copy method signatures, error handling patterns
```

---

### **apex-android** (Python, security gates + testing)
**Status:** Mature Android security scanning tool. 2000+ LOC.  
**Relevance:** Security gate infrastructure, test patterns, CLI structure.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `cursor_gate.py` security checklist | Pre-commit security gate for all CA projects (#2–#10) | ALL SLICES | No eval/exec/pickle, no secrets, async safety—already automated |
| Test structure (`tests/test_*.py`) | Unit test patterns for CA logic validation | ALL SLICES | Pytest infrastructure, mocking patterns for generators |
| `setup.py` + PyPI workflow | Package repurpose-engine + CA tools for distribution | Post-MVP | Entry points, console scripts, version mgmt |

**Why:** Security gates are non-negotiable in your system. Copy-paste ready.

**Ship plan:**
```bash
# apex-android/cursor_gate.py → all-ca-projects/
# Use verbatim in pre-commit hook
# Adapt test structure from apex-android/tests/ → ca-dungeon-gen/tests/
```

---

### **frontier-syntax** (Rust, 3.8K LOC across modules)
**Status:** DEX parser, optimizer, neural engine. Formally-verified language.  
**Relevance:** Parser architecture, rule validation, caching, optimization patterns.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `parser.rs` structure (pattern matching, error recovery) | Parse CA rule strings (e.g., "23/3" → (birth, death) tuples) | #2 SLICE_001 | Adapt: 23/3 notation (Conway birth/death) vs other rule formats |
| `ast.rs` + `ir.rs` (Intermediate Representation) | Represent CA state as AST (grid → rule application graph) | #2 SLICE_003 | Reuse traversal patterns for rule validation |
| `optimizer.rs` (performance tuning) | Optimize CA grid iteration (1000+ cells, 60 FPS target) | #3 SLICE_101 | Profile + inline hot paths—copy methodology |
| `cache.rs` (caching layer) | Cache CA generation results (seed → cave tilemap LRU) | #2 SLICE_004 | Avoid recomputing identical seeds |
| `verifier.rs` (correctness proofs) | Validate cave connectivity, no-dead-end checker | #2 SLICE_005 | Adapt: proof automation for CA correctness |

**Why:** Rust parser is overkill for CA; Python equivalent is simpler. But patterns transfer directly (AST node types, error recovery, caching).

**Ship plan:**
```rust
// frontier-syntax/frontier-dex/src/parser.rs → python adapter for CA rule parsing
// Adapt regex-based parser to parse CA rule notation (e.g., "B23/S3")
// Reuse: cache.rs → ca-dungeon-gen/cache.py
```

---

### **gutterumble** (Godot 4, 60 FPS multiplayer game)
**Status:** Shipped beta Android app. Supabase backend.  
**Relevance:** Godot architecture, networking, asset pipeline, performance optimization.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `net/lobby_manager.gd` (multiplayer) | Adapt for #10 (EdTech leaderboard sync, cross-device puzzle state) | #10 SLICE_008 | User quiz scores → persistent Supabase table |
| `autoloads/` pattern (singletons) | Global autoload for CA engine state (rule cache, seed history) | #2, #3 SLICE_001 | `autoloads/ca_engine.gd` for Godot integration |
| `scenes/test/` (test scenes) | Godot test scene framework for CA tilemap validation | #2 SLICE_007 | Load generated caves, verify 60 FPS, no crashes |
| `backend/supabase_manager.gd` + schema | Reuse Supabase auth + DB schema for #10 (user puzzles, scores) | #10 SLICE_001 | Copy table definitions: `users`, `puzzle_completions` |
| `export_presets.cfg` (Android build) | Reuse proven Android export config (60 FPS, physics settings) | #2, #3 Android | No Vulkan/threaded optimization—known stable |

**Why:** GUTTERUMBLE is production Android. Schema, autoload patterns, performance tuning are battle-tested.

**Ship plan:**
```gdscript
// gutterumble/autoloads/ → ca-crowd-sim/autoloads/ca_engine.gd
// Copy structure, adapt for CA state management instead of combat
// gutterumble/backend/supabase_manager.gd → edu-playground/backend/
```

---

## TIER-2: ADAPTATION REQUIRED (Ship in Slice 011–050)

### **prjctnxs** (Rust ECS engine, nexus-runtime)
**Status:** Game engine with physics, entity management. Performance-critical.  
**Relevance:** ECS architecture, physics simulation, benchmarking infrastructure.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `ecs/mod.rs` (Entity-Component-System) | Base for #3 CA crowd sim (entities = agents, components = position/velocity/ca_state) | #3 SLICE_100 | Adapt ECS pattern: agent = entity, CA rule = system |
| `engine/mod.rs` (game loop + fixed timestep) | 1024 Hz target loop for CA rule application per frame | #3 SLICE_101 | Copy `GameLoop::bench_ticks()` for FPS profiling |
| `gpu/mod.rs` (GPU acceleration stub) | Future optimization: compute shader for 10K+ agents (#3 SLICE_102) | Backlog | Out of scope for MVP; document as optimization path |
| Benchmarking patterns (`benches/`) | Profile CA generation (target: < 100ms for 50×50 cave) | #2 SLICE_006 | Adapt: bench_ticks() → ca_cave_bench() |

**Why:** ECS is overkill for #2 (dungeon). Perfect for #3 (crowd sim with 1000 agents). Transferable patterns.

**Ship plan:**
```rust
// Rewrite ECS logic in Python for CA dungeon (too complex for MVP)
// Adapt for #3 crowd sim in Godot: component-based agent architecture
// prjctnxs/benches/ → ca-crowd-sim/benches/
```

---

### **mia.loa** (Web LLM, mobile companion)
**Status:** Shipped mobile + web. WebLLM bridge for on-device inference.  
**Relevance:** Mobile web bridging, on-device LLM, state sync.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| `public/webllm.js` (browser LLM) | Run tiny LLM for #10 (quiz hint generation, on-device) | #10 SLICE_011 (future) | Optional: LLM hints for educational puzzles; ship without in MVP |
| `mobile/capacitor/` (native bridge) | If #10 ships as mobile (React Native)—capacitor plugins already exist | #10 SLICE_014 (mobile port) | Out of scope for MVP; web-first |
| Service worker (`public/sw.js`) | Offline support for #10 (cached puzzles, works without network) | #10 SLICE_012 | Enable offline quiz completion → sync when online |

**Why:** On-device LLM + offline support are 10x differentiators. But not MVP-blocking; backlog for Phase 2.

**Ship plan:**
```javascript
// mia.loa/public/sw.js → edu-playground/public/sw.js
// Adapt: cache puzzle definitions, enable offline play
```

---

### **frontier-syntax IDE** (Empty/Stub)
**Status:** WIP, no code yet.  
**Relevance:** None (no salvageable code).

---

## TIER-3: PATTERNS ONLY (No code reuse, but methodology applies)

### **bookish-bassoon** + **apktool-diagnostics** (Minimal stubs)
**Status:** Placeholder repos with `cursor_gate.py` boilerplate only.  
**Relevance:** Process/testing framework template only.

| Salvage | Use Case | Slice | Notes |
|---------|----------|-------|-------|
| Repo structure (LICENSE, README, tests/) | Template for new CA projects | All | Copy directory layout, .gitignore, CI config |
| `samples/hello_passing.py` pattern | Test structure template | All | Adapt for CA-specific test cases |

---

## SALVAGE ROADMAP (By Slice)

### **Phase 0: Core Algorithm (Weeks 1–2)**

```
SLICE_001 (CA cave rules):
  ✅ Copy: repurpose-engine/repurpose.py → validators.py (clean_transcript → validate_ca_rules)
  ✅ Copy: frontier-syntax/frontier-dex/src/parser.rs pattern → ca_parser.py
  ✅ Copy: apex-android/cursor_gate.py → security_gate (mandatory)
  ✅ Reference: frontier-syntax/frontier-dex/src/ir.rs → CA state representation

SLICE_002 (Tilemap JSON):
  ✅ Reference: gutterumble/docs/arena_manifest.json (format template)
  ✅ Adapt: repurpose-engine/truncate_to_limit() for output size validation

SLICE_003 (Python CLI):
  ✅ Copy: repurpose-engine/main() (argparse structure)
  ✅ Reference: apex-android/setup.py entry points for console script

SLICE_004 (Connectivity checker):
  ✅ Copy: frontier-syntax/frontier-dex/src/verifier.rs logic (proof patterns)
  ✅ Adapt: prjctnxs/engine/mod.rs loop structure for graph traversal

SLICE_005 (Difficulty scorer):
  ✅ Reference: prjctnxs/benches/ profiling patterns
  ✅ No direct code reuse; novel algorithm
```

### **Phase 1: Godot Integration (Weeks 2–3)**

```
SLICE_006 (GDScript wrapper):
  ✅ Copy: gutterumble/autoloads/network_manager.gd subprocess pattern
  ✅ Copy: gutterumble/project.godot build settings (Python subprocess calls)

SLICE_007 (Tilemap painter):
  ✅ Copy: gutterumble/scenes/arenas/ (tilemap scenes, collision setup)
  ✅ Reference: gutterumble/export_presets.cfg (Android export config)

SLICE_008 (GUTTERUMBLE integration):
  ✅ Copy: gutterumble/scenes/arenas/ tilemap instantiation pattern
  ✅ Copy: gutterumble/autoloads/game_manager.gd arena loading

SLICE_009 (GitHub public release):
  ✅ Copy: bookish-bassoon/ repo structure (LICENSE, README template)
  ✅ Copy: apex-android/ test structure

SLICE_010 (Security gate):
  ✅ Copy: apex-android/cursor_gate.py (verbatim)
```

### **Phase 2: Validation & Ship (Weeks 3–4)**

```
SLICE_100–103 (CA Crowd Sim — parallel track):
  ✅ Copy: prjctnxs/engine/mod.rs game loop + benchmark
  ✅ Copy: pettu/src/stores/ state management pattern (if web UI)
  ✅ Adapt: prjctnxs/ecs/mod.rs → agent-based architecture
```

### **Phase 3: Pattern Evolution (#4)**

```
SLICE_200–203 (GA + web UI):
  ✅ Copy: pettu/src/stores/companionStore.ts → evolutionStore.ts
  ✅ Copy: mia.loa/public/sw.js → offline support (Phase 2)
  ✅ Reference: frontier-syntax/frontier-dex/src/optimizer.rs mutation patterns
```

### **Phase 4: EdTech Playground (#10)**

```
SLICE_300–310 (Quiz + leaderboard):
  ✅ Copy: gutterumble/backend/supabase_manager.gd → Supabase schema
  ✅ Copy: gutterumble/net/lobby_manager.gd → leaderboard sync
  ✅ Copy: pettu/src/stores/companionStore.ts → questStore.ts (quiz state)
  ✅ Copy: mia.loa/public/sw.js → offline quiz caching
```

---

## SECURITY GATES (All Phases)

**Copy verbatim from apex-android/cursor_gate.py:**

```
[ ] No secrets (grep -r "sk_", "password", "api_key", ".env")
[ ] No unsafe execution (grep -rE "(eval|exec|shell=True|os\.system)")
[ ] No bad deserialization (grep -rE "(pickle|yaml\.load\(|marshal)")
[ ] No unvalidated input (CA rules must be integers 0–255)
[ ] No sensitive data in logs
[ ] No async/thread race conditions
```

**Run before every merge:**
```bash
python3 cursor_gate.py --file <slice> --iterations 3
```

---

## Code Debt Warnings

| Repo | Issue | Impact | Mitigation |
|------|-------|--------|-----------|
| frontier-syntax | Formal verification claims not validated during reuse | Medium | Copy only parser logic; ignore correctness claims |
| gutterumble | Heavy asset dependencies (48M textures, characters) | Low | Use only GDScript autoload patterns; exclude assets |
| pettu | Supabase/TanStack Query client side config | Medium | #10 must configure own Supabase project; don't assume schema |
| prjctnxs | ECS architecture is game-engine-specific | Medium | Adapt for #3 only; #2 simpler data structure sufficient |
| apex-android | Android-specific CVE/SBOM logic | Low | Use only cursor_gate.py and test patterns; ignore Android-specific tools |

---

## TL;DR – Copy These Files Verbatim

```
repurpose-engine/repurpose.py → ca-dungeon-gen/validators.py
apex-android/cursor_gate.py → .pre-commit-hooks.yaml (all projects)
apex-android/tests/ → ca-dungeon-gen/tests/ (pytest patterns)
apex-android/setup.py → ca-dungeon-gen/setup.py (PyPI entry point)
pettu/src/stores/companionStore.ts → pattern-evolution/stores/evolutionStore.ts
gutterumble/autoloads/network_manager.gd → ca-dungeon-gen/autoloads/ca_engine.gd (pattern only)
gutterumble/backend/supabase_manager.gd → edu-playground/backend/ (pattern only)
```

---

## Next Step

Pick one slice from Phase 0 above. Verify code can be copied (no private data, no company-specific logic). Ship it. Validate. Move to next slice.

**Start:** SLICE_001 (CA rules + validator). Estimated: 2 hours (parser + 20 unit tests).
