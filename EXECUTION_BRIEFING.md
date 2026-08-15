# 🚀 EXECUTION BRIEFING – Ship All 4 Projects ASAP

**Generated:** 2026-08-14  
**Mode:** AGGRESSIVE CONTINUOUS (No timetable, no breaks, ASAP cadence)  
**Owner:** AFg  
**Status:** Ready to launch NOW  

---

## THE PLAN (1-Page Summary)

You're building **4 CA-powered projects** using **One Core CA Engine** (#2 CA Dungeon Gen) that powers all downstream projects (#3 Crowd Sim, #4 Pattern Evo, #10 EdTech).

**Critical Path:**
```
Phase 0 (6h) → Phase 1 (6h) → Phase 2 (5h) → Phase 3 (3h)
    ↓ DONE
    └─ SHIP #2 (CA Dungeon Gen)
       └─ Phase 4 starts (parallel) + Phase 5 queued
          ├─ SHIP #3 (CA Crowd Sim) 
          └─ SHIP #4 (Pattern Evolution)
             └─ SHIP #10 (EdTech)
```

**Total Estimated:** 20–30 hours of focused work → 4 shipped projects  
**Ship Velocity:** 1 project per 5–8 hours of execution  

---

## YOUR 6 FILES (READ THESE IN ORDER)

### 1. 📋 **PROJECT_STATE.md** (Start here every session)
- **What it is:** Real-time tracking of all slices + phases + blockers
- **How to use:** Check current slice status, update when done, move to next
- **Updated:** After each slice completes (5 min update)

### 2. 🛣️ **UNIFIED_ROADMAP.md** (Your master blueprint)
- **What it is:** All 6 phases, all edge cases, all smoke tests
- **How to use:** Reference for what to build, expected behavior, edge cases to test
- **Updated:** Never (this is your contract with yourself)

### 3. 🧪 **SMOKE_TEST_LOG.md** (Your proof-of-work)
- **What it is:** Template for recording test results after each slice
- **How to use:** Copy test output → paste here → mark ✅ PASS or ❌ FAIL
- **Updated:** After every slice's smoke test (copy-paste command output)

### 4. 💻 **CLAUDE_CODE_PROMPT.md** (Paste into Claude Code NOW)
- **What it is:** Ready-to-paste prompt for building SLICE_RES_001 (CA engine)
- **How to use:** Copy entire thing → Open Claude Code → Paste → Run → Ship
- **This launches:** SLICE_RES_001 (ca_engine.py + tests)

### 5. 🔧 **CODE_SALVAGE.md** (For later phases)
- **What it is:** Which files to copy from your 10 repos into each slice
- **How to use:** Reference when starting Phase 1+ (tells you what to reuse)
- **Updated:** Never (static reference)

### 6. 💰 **BUSINESS_ALTERNATIVES.md** (Revenue plan, read later)
- **What it is:** 15 monetization ideas from your code patterns
- **How to use:** Read after #2 ships (not blocking development)
- **Updated:** Never (static reference)

---

## STEP-BY-STEP: WHAT TO DO RIGHT NOW

### STEP 1: Open Claude Code (5 min)
1. Open Claude Code (desktop app or mobile)
2. Create new session
3. Paste **entire** CLAUDE_CODE_PROMPT.md into the chat

### STEP 2: Build SLICE_RES_001 (2–3 hours)
Claude Code will generate:
- `ca_engine.py` (core CA logic, 500 LOC)
- `test_ca_engine.py` (10 unit tests)
- README with examples

You're done when Claude Code returns test output showing all tests pass.

### STEP 3: Run Smoke Test (10 min)
Copy-paste this command:
```bash
python3 test_ca_engine.py --smoke-bulk --count 50 --max_time 100
```

Expected output:
```
Generated 50 caves in 87ms (avg 8.7ms/cave) ✅
```

### STEP 4: Record Results (5 min)
Go to SMOKE_TEST_LOG.md:
- Find "SMOKE_RES_001 – CA Engine Spike"
- Paste test output into "Actual Output"
- Mark status: ✅ PASS
- Update PROJECT_STATE.md: Mark SLICE_RES_001 as ✅ COMPLETE

### STEP 5: No Breaks – Move to SLICE_RES_002 (Immediately)
Go to CLAUDE_CODE_PROMPT.md, find the **connectivity.py spike** section.
Open a fresh Claude Code session, paste the connectivity spike prompt, repeat steps 2–4.

### STEP 6: Repeat Until Phase 0 Exits (Continuous)
```
SLICE_RES_001 ✅ → SLICE_RES_002 ✅ → SLICE_RES_003 ✅ → EXIT GATE CHECK
```

**NO WAITING between slices.** This is continuous execution.

---

## EXECUTION RULES (Non-Negotiable)

### ✅ DO THIS:
- **Execute immediately.** Don't plan, don't overthink. Start SLICE_RES_001 now.
- **Back-to-back slices.** Finish → Smoke test → Record → Next slice (same session).
- **Paste test output verbatim.** No summaries, no editing. Exact command output.
- **Ship when gate passes.** Don't iterate. Don't perfect. Exit gate ✅ = ship immediately.
- **Parallel when possible.** Start Phase 4 while Phase 3 docs finalize (no waiting).

### ❌ DON'T DO THIS:
- **Don't ask for permission.** Your shipping OS says "go," go now.
- **Don't break between phases.** No "let me think about this." Code → test → next.
- **Don't rewrite code.** If tests pass, it ships. No perfectionism.
- **Don't wait for feedback.** Post to r/gamedev the day Phase 3 exits. Get engagement metrics.
- **Don't abandon slices mid-build.** Finish → test → record → done. Always.

---

## EDGE CASES YOU'LL HIT (And How to Handle Them)

### "The CA engine generates weird-looking caves"
**Expected:** ~50% will look organic, 30% will be isolated islands, 20% will be unusable  
**Action:** That's normal. Connectivity checker (SLICE_RES_002) handles isolation. Difficulty scorer (SLICE_005) rejects unplayable ones. Don't overthink it.

### "Godot can't find Python executable"
**Expected:** Subprocess path issues on Windows/Mac  
**Fix:** Use absolute Python path in ca_bridge.gd (hardcode it if needed)  
**Test:** `python3 -c "print('ok')"` in Git Bash first

### "FPS drops to 45 at 1000 agents"
**Expected:** That's Phase 3 crowd sim, normal on mid-range hardware  
**Fix:** Spatial partitioning (SLICE_102) solves it  
**Target:** 55+ FPS with partitioning (acceptable, not gorgeous)

### "GA keeps converging to same pattern every run"
**Expected:** Non-determinism is annoying but harmless  
**Fix:** Expose seed parameter to user (let them control it)  
**Rule:** Ship it anyway. Reproducibility is Phase 2 polish, not Phase 1 blocker

### "Leaderboard sync takes 5+ seconds"
**Expected:** Supabase cold start or network latency  
**Fix:** Connection pooling, pre-warm DB, use edge functions instead of REST  
**Target:** < 2 seconds (test with 50 concurrent users in Phase 6)

---

## SUCCESS METRICS (What "Done" Looks Like)

### Phase 0 ✅
- 3 spikes build without crashes
- 3 smoke tests all ✅ PASS
- Exit gate passes

### Phase 1 ✅
- 5 slices ship
- 50 caves generate error-free
- Connectivity validates 95%+ accuracy
- Performance < 100ms total

### Phase 2 ✅
- Python ↔ Godot bridge works (0 crashes in 20 calls)
- Tilemap renders 60 FPS
- GUTTERUMBLE integration tested

### Phase 3 ✅
- GitHub repo public
- README complete with examples
- Posted to r/gamedev (target: 50+ upvotes or 100+ downloads in 48h = traction)

### Phase 4 ✅ (parallel)
- 1000 agents render 55+ FPS
- Emergent crew behavior (no hand-coded state machines)

### Phase 5 ✅
- GA evolves patterns in < 50 generations
- Web UI responsive and beautiful
- Pattern export works (PNG, GIF, SVG)

### Phase 6 ✅
- 10 puzzles playable
- Leaderboard syncs < 2s (50 users)
- Mobile export 45+ FPS
- Posted to App Store + Google Play (launch day, don't wait for polish)

---

## WHAT YOU'LL SHIP (The Actual Deliverables)

### Ship 1: CA Dungeon Gen (#2) – Week 1
```
GitHub repo (public)
├─ ca_engine.py (core)
├─ validators.py
├─ connectivity.py
├─ difficulty.py
├─ tilemap.py
├─ tests/ (all tests)
├─ examples/ (50 pre-generated caves)
├─ godot/ (Godot integration)
└─ README.md (5 examples)

Platforms:
- Godot Asset Store listing
- Gumroad ($9.99/mo)
- GitHub free + open-source
```

### Ship 2: CA Crowd Sim (#3) – Week 2
```
Integrated into GUTTERUMBLE
├─ crowd_engine.py
├─ crowd_renderer.gd
├─ GUTTERUMBLE crew behavior (via CA)
└─ Tests + smoke tests

Launch:
- GitHub release
- Integration blog post
- r/gamedev post
```

### Ship 3: Pattern Evolution (#4) – Week 3
```
Web app (React + Three.js)
├─ GA engine (Python backend)
├─ UI (React/TypeScript)
├─ Export (PNG, GIF, SVG)
├─ Preset library (user-created patterns)
└─ Tests + smoke tests

Launch:
- evolution.yoursite.com (live)
- Product Hunt launch (1st day)
- r/generativeart post
```

### Ship 4: EdTech Playground (#10) – Week 4–5
```
Mobile app + Web
├─ 10 CA puzzles (Godot)
├─ Leaderboard (Supabase)
├─ Teacher dashboard (React)
├─ Hints + guidance system
├─ iOS + Android export
└─ Tests + smoke tests

Launch:
- App Store + Google Play (day 1 beta)
- Free tier + school licensing ($500/year)
- Reach out to 5 Orange County schools (APG angle)
- Twitter + education hashtags
```

---

## YOUR WEAPONS (What Makes This Possible)

### Code Salvage
- ✅ repurpose-engine (validators logic)
- ✅ apex-android (security gates + tests)
- ✅ gutterumble (Godot patterns, Supabase schema)
- ✅ pettu (state management in React/TypeScript)
- ✅ frontier-syntax (parser patterns)
- ✅ prjctnxs (ECS/game loop patterns)

### Research Validated
- ✅ Web search completed (edge cases documented)
- ✅ Disconnected cave handling (horizontal blanking solution exists)
- ✅ GA convergence (diversity injection + mutation rate adaptation)
- ✅ Godot mobile perf (spatial partitioning, VRAM compression)
- ✅ Flocking behavior (Boids reference, settled algorithm)

### Your Shipping OS (Preferences)
- ✅ 15-gate review system (cursor_gate.py)
- ✅ Phase completion gates (binary: ship or hold)
- ✅ Smoke tests after every phase (go/no-go)
- ✅ Security-first (no eval/exec/pickle/secrets)
- ✅ Roadmap binding (every feature ships or phase doesn't close)

---

## WHAT NOT TO DO (Failure Modes to Avoid)

### ❌ "Let me plan this more"
**Result:** You'll miss momentum. Shipping OS says "go now." Go.

### ❌ "Let me polish the CA engine before moving to Godot"
**Result:** Phase bloat. If tests pass, it's good enough. Godot integration will expose real issues.

### ❌ "I'll wait for feedback before shipping to Reddit"
**Result:** Perfectionism kills momentum. Post day-of-release. Iterate on feedback in v1.1.

### ❌ "Let me rewrite this slice, the code quality isn't great"
**Result:** Technical debt paralysis. Code that ships beats perfect code that doesn't. Refactor post-MVP.

### ❌ "I should do Phase 3 really well before Phase 4"
**Result:** Unnecessary serialization. Phases 3 + 4 are parallel. Start Phase 4 while Phase 3 docs finalize.

---

## YOUR NEXT 10 MINUTES (Right Now)

1. **Open Claude Code** (1 min)
2. **Copy CLAUDE_CODE_PROMPT.md entire text** (1 min)
3. **Paste into Claude Code** (1 min)
4. **Run it** (execute the code generation) (7 min)

**After that:** Smoke test → Log results → Next slice (no breaks).

---

## EMERGENCY CONTACTS (If Stuck)

- **Can't build something:** Check UNIFIED_ROADMAP.md for edge cases. Check CODE_SALVAGE.md for reusable code.
- **Test fails:** Check UNIFIED_ROADMAP.md for known issues + mitigations.
- **Performance slow:** Check web search results (Godot mobile perf, GA convergence, cave connectivity).
- **Phase blocked:** Check PROJECT_STATE.md for current blocker list.
- **Not sure what to build:** Check CLAUDE_CODE_PROMPT.md (for Phase 0/1) or appropriate phase in UNIFIED_ROADMAP.md.

---

## FINAL PREACH

Your shipping OS is a contract with yourself:
- **Roadmap binding** = ship everything or phase doesn't close
- **Security-first** = no shortcuts on safety
- **Smoke tests** = go/no-go gates, no partial passes
- **Continuous execution** = no breaks between phases
- **Ship when gate passes** = no perfection, no iteration, SHIP

This works because:
1. Clear, measurable exit gates (not subjective "good enough")
2. Parallel phases wherever possible (Phases 3 + 4 overlap)
3. Reusable code (CODE_SALVAGE.md reduces build time)
4. Edge case prep (web research embedded in roadmap)
5. Ruthless scope (ship 4 products, not 40 features)

**You will ship all 4 projects because the gates are binary.** ✅ = ship. ❌ = fix + retest. No "good for now."

---

## LET'S GO

🚀 **Start SLICE_RES_001 now.** You've got this.

**Your First Command (Copy-Paste This):**
```
Open Claude Code → Paste CLAUDE_CODE_PROMPT.md → Hit Run
```

**You'll have working code in 3 hours.**  
**You'll have #2 shipping in ~24 hours of focused work.**  
**You'll have all 4 projects shipped in 20–30 hours.**

No waiting. No planning paralysis. No perfectionism.

Just build, test, ship, repeat.

---

**Generated:** 2026-08-14  
**Version:** 1.0 (Ready for launch)  
**Status:** 🚀 GO NOW

