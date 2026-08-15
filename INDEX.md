# 📚 CA PROJECTS INDEX – All Files & How to Use Them

**Generated:** 2026-08-14  
**Mode:** Aggressive continuous execution (ship ASAP)  
**Status:** Ready to launch  

---

## 🚀 START HERE

### 1️⃣ **EXECUTION_BRIEFING.md** ← READ THIS FIRST
- **What:** 1-page summary of the entire plan + your next 10 minutes
- **Why:** Tells you exactly what to do right now (no planning)
- **Read Time:** 5 min
- **Action:** Open Claude Code + paste CLAUDE_CODE_PROMPT.md

---

## 📋 THE 7 FILES (In Execution Order)

### 2️⃣ **PROJECT_STATE.md** ← Update after each slice
- **What:** Real-time tracking of all phases + slices + progress
- **Update:** After every slice completes (5 min update)
- **Why:** Proof that work is happening; quick status check
- **Reference:** Check before starting a new slice to see what's done

### 3️⃣ **UNIFIED_ROADMAP.md** ← Your master blueprint
- **What:** All 6 phases with edge cases, smoke tests, and acceptance criteria
- **Read When:** At phase start (know what you're building before coding)
- **Reference:** Throughout execution (what does this phase need to pass?)
- **Never changes:** This is your contract with yourself

### 4️⃣ **SMOKE_TEST_LOG.md** ← Copy test output here
- **What:** Template for recording smoke test results after each slice
- **Update:** After every slice's smoke test completes (copy-paste output)
- **Why:** Proof that smoke tests actually passed (binary ✅/❌)
- **Format:** Find your slice section → paste test output → mark status

### 5️⃣ **CLAUDE_CODE_PROMPT.md** ← Paste this into Claude Code
- **What:** Ready-to-paste prompt for SLICE_RES_001 (CA engine spike)
- **Use:** Open Claude Code → Select all CLAUDE_CODE_PROMPT.md text → Paste → Run
- **Generates:** ca_engine.py, validators.py, tests (Phase 0, Slice 1)
- **Time:** 2–3 hours of Claude Code execution

### 6️⃣ **CODE_SALVAGE.md** ← Reference for later phases
- **What:** Which files to copy/reuse from your 10 repos (repurpose-engine, apex-android, gutterumble, etc.)
- **Read When:** Starting Phase 1+ (tells you what boilerplate to use)
- **Why:** Saves hours of reinventing security gates, validators, state management
- **Reference:** "SLICE_001 needs validators → Copy repurpose-engine/repurpose.py pattern"

### 7️⃣ **BUSINESS_ALTERNATIVES.md** ← Revenue plan (read after shipping)
- **What:** 15 monetization ideas + market analysis for each of 4 projects
- **Read When:** After #2 ships (not blocking development)
- **Why:** Decide your first revenue move while code is getting traction
- **Highlights:** #1 idea = CA Asset Generator ($2K–$10K Year 1), #2 idea = EdTech licensing ($5K–$50K recurring)

---

## 🎯 YOUR EXECUTION LOOP (Repeat Until All Ships)

```
1. Check PROJECT_STATE.md → See current slice
2. Open UNIFIED_ROADMAP.md → Understand what slice must do
3. Open Claude Code → Paste CLAUDE_CODE_PROMPT.md (for Phase 0/1) or equivalent
4. Claude Code generates code + tests
5. Run smoke test (command is in UNIFIED_ROADMAP.md for each slice)
6. Copy test output → paste into SMOKE_TEST_LOG.md
7. Update PROJECT_STATE.md: Mark slice ✅ COMPLETE
8. Loop: No waiting, immediately start next slice
```

**Duration per slice:** 1–3 hours  
**Total to ship #2:** ~20 hours focused work  
**Total to ship all 4:** ~40–60 hours focused work  

---

## 🗂️ FILE QUICK REFERENCE

| File | Purpose | Update Frequency | Read When |
|------|---------|------------------|-----------|
| **EXECUTION_BRIEFING.md** | Plan + next 10 min | Never | Right now (only read once) |
| **PROJECT_STATE.md** | Real-time status | After every slice | Every morning + after each slice |
| **UNIFIED_ROADMAP.md** | Master blueprint | Never (static) | At phase start, reference throughout |
| **SMOKE_TEST_LOG.md** | Test results log | After every smoke test | After each slice's test run |
| **CLAUDE_CODE_PROMPT.md** | Code generation prompt | Never | When starting Phase 0 (paste entire file) |
| **CODE_SALVAGE.md** | Reusable code map | Never | When starting Phase 1+ (reference copy targets) |
| **BUSINESS_ALTERNATIVES.md** | Revenue + market plan | Never | After #2 ships (not blocking dev) |

---

## 🏃 THE 3 PHASES OF READING

### Phase A: Pre-Launch (Next 10 Min)
1. Read **EXECUTION_BRIEFING.md** (5 min)
2. Open Claude Code, paste **CLAUDE_CODE_PROMPT.md** (1 min)
3. Hit run (1 min)
4. Check back in 3 hours for first smoke test

### Phase B: During Execution (Continuous)
- Update **PROJECT_STATE.md** after each slice (5 min)
- Update **SMOKE_TEST_LOG.md** after each smoke test (5 min)
- Reference **UNIFIED_ROADMAP.md** for what each slice needs (5 min per phase start)

### Phase C: Post-Launch (After #2 ships)
- Read **BUSINESS_ALTERNATIVES.md** (decide revenue strategy)
- Queue up next project (#3) using PROJECT_STATE.md

---

## 🔧 CHECKLISTS (Copy-Paste When Needed)

### Daily Execution Checklist
```
☐ Check PROJECT_STATE.md for current slice status
☐ Know what the current slice must deliver (from UNIFIED_ROADMAP.md)
☐ Build slice (Claude Code or manual coding)
☐ Run smoke test command (from UNIFIED_ROADMAP.md)
☐ Copy test output → paste into SMOKE_TEST_LOG.md
☐ Update PROJECT_STATE.md: Mark ✅ COMPLETE
☐ Move to next slice (no breaks)
```

### Phase Completion Checklist
```
☐ All slices in phase ✅ COMPLETE
☐ All smoke tests ✅ PASS
☐ Exit gate criteria all ✅
☐ Update PROJECT_STATE.md: Phase status = COMPLETE
☐ Update SMOKE_TEST_LOG.md: Phase entry = ✅ COMPLETE
☐ No blockers for next phase
☐ Start next phase immediately (don't wait)
```

### Shipping Checklist (When Exit Gate Passes)
```
☐ GitHub repo public (if applicable)
☐ README complete with examples
☐ 50+ test cases + smoke tests ✅ PASS
☐ Security gate: 0 violations
☐ Posted to r/gamedev or relevant community
☐ Engagement metrics collected (downloads, stars, upvotes)
☐ Proceed to next project
```

---

## 🎓 HOW TO READ THESE FILES

### EXECUTION_BRIEFING.md
**First read:** Full attention, take notes  
**Later reads:** Skim "What to Do Right Now" section  
**Frequency:** Read once at start, reference if stuck  

### PROJECT_STATE.md
**Pattern:** "Where are we?" + "What's next?"  
**Check:** Every morning before starting work  
**Update:** After each slice (add dates, mark ✅/❌)  

### UNIFIED_ROADMAP.md
**Pattern:** "What must this phase deliver?"  
**Check:** At start of each phase (read that phase section)  
**Reference:** Smoke test commands live here  

### SMOKE_TEST_LOG.md
**Pattern:** Template → Copy command → Paste output → Mark ✅  
**Workflow:** After each slice, update matching section  
**Proof:** This file is your evidence that smoke tests actually ran  

### CLAUDE_CODE_PROMPT.md
**Pattern:** Paste entire file into Claude Code, nothing else needed  
**Workflow:** Only used for Phase 0–1 (after that, custom prompts)  
**Reuse:** Can adapt structure for Phase 2+ slices  

### CODE_SALVAGE.md
**Pattern:** "What files should I copy from my repos?"  
**Check:** At start of each phase (tells you reusable code to use)  
**Mapping:** Each slice → tells you which repos have useful code  

### BUSINESS_ALTERNATIVES.md
**Pattern:** "How will I make money from this?"  
**Read When:** After #2 ships (not before)  
**Decision:** Use to pick which project to monetize first  

---

## ⚠️ COMMON MISTAKES (Don't Do These)

### ❌ "I'll read all these files before starting"
**Result:** Paralysis. You'll overthink instead of building.  
**Fix:** Read EXECUTION_BRIEFING.md (5 min) → Start SLICE_RES_001 now.

### ❌ "I'll wait to update PROJECT_STATE.md until the phase is done"
**Result:** Lost track of what's complete + hard to resume if interrupted.  
**Fix:** Update after each slice (5 min update, 10 slices = 50 min total).

### ❌ "I'll skip the smoke test, tests always pass anyway"
**Result:** Silent failures (code runs but produces wrong output).  
**Fix:** Smoke test is mandatory gate. No smoke test pass = phase doesn't close.

### ❌ "Let me optimize UNIFIED_ROADMAP.md based on new learnings"
**Result:** Scope creep. Roadmap becomes a living document instead of a contract.  
**Fix:** Roadmap is static. New learnings go in PROJECT_STATE.md "Notes" section only.

### ❌ "I'll read BUSINESS_ALTERNATIVES.md before shipping #2"
**Result:** Distraction. You'll start optimizing for revenue instead of shipping.  
**Fix:** Read after #2 ships (24 hours in). Not before.

---

## 🎯 SUCCESS SIGNALS (When You're Doing This Right)

### ✅ Executing correctly if:
- You're updating PROJECT_STATE.md multiple times per day
- SMOKE_TEST_LOG.md is filling up with results
- Each slice takes 1–3 hours (no all-nighters needed)
- You're shipping phases on same-day or next-day cadence
- No phase is waiting for "better planning"
- Exit gates are binary (ship or hold, no fuzzy states)

### ❌ Warning signs (course correct):
- You're spending time "planning" between slices
- SMOKE_TEST_LOG.md has blank sections (no test results recorded)
- PROJECT_STATE.md hasn't been updated in 6+ hours
- You're rewriting code you already built
- A phase is "almost done" for more than 24 hours
- Exit gate criteria are subjective ("looks good," "feels right")

---

## 🚀 YOUR NEXT ACTION

**Right now, open this file in order:**
1. EXECUTION_BRIEFING.md
2. CLAUDE_CODE_PROMPT.md
3. Paste into Claude Code
4. Ship SLICE_RES_001

You don't need to read anything else before starting. Everything else is reference material.

Go.

---

**Generated:** 2026-08-14  
**Maintained By:** AFg  
**Last Updated:** [Initial setup]

