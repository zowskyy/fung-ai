# NO SAND BEACH — Sequence Breakdown

Maps each of the 7 sequences to the characters, locations, and animation states asset production needs to cover. Sequence 1 has a full 17-beat breakdown (`scenes/sequence_01_setup_breakdown.md`) and is production-ready. Sequences 2–7 below are scoped from the master story (`script.md`) but not yet broken into beats — treat their contents as planning input, not final dialogue/timing.

---

## Visual Style Reference: Menace II Society

NO SAND BEACH takes visual and tonal direction from *Menace II Society* (1993). This applies at two levels:

**1. Throughout the whole film (homage, not literal setting):** NO SAND BEACH stays contemporary and stays in Santa Ana — the app, the background checks, the modern courtroom all remain as written. What carries over from M2S is *cinematography and character archetype*: tight, hardened-realism framing; high-contrast black-and-white compositions that favor faces and body language over wide spectacle; unhurried, weighted staging (characters occupy space like the environment costs them something); the sense that every character is carrying consequence, not just reacting to plot. Marcus's "I had to be perfect" resentment and Earl's "loved the street more" tragedy are exactly the moral-weight-of-choices register M2S's Caine/O-Dog/Pernell dynamic operates in — lean into that when staging their scenes, not just their dialogue.

**2. Literal early-90s period styling for two specific beats:** Earl's flashback (Sequence 1, Beat 1.14) and all of Sequence 2 ("The Fall" — arrest, prison) get period-accurate wardrobe, environment, and staging referencing M2S directly, since these are the film's street-life-and-incarceration beats. This is a deliberate stylized choice, not literal chronology — the flashback's real in-story date (Pure would have been 7 sometime in the last ~20-25 years relative to his present-day 30s) doesn't necessarily land in the actual early 90s. Treat it the way many contemporary films treat a "timeless slum aesthetic": intentional, not a continuity error to fix.

**Production implication:** Earl's design and Pure's teen/21yo prison-era designs need two passes each if strict continuity ever matters later — but for this production, one M2S-styled design per character/beat is sufficient unless a future sequence needs to show the same character in both a contemporary and period context side by side (not currently the case).

---

## Sequence 1: The Setup ✅ Beats authored (17 beats, 2:45)

- **Locations:** Santa Ana apartment (interior, night & morning), kitchen, bedroom, school playground, school building (establishing), aerial Santa Ana (drone/sunset)
- **Characters:** Delia (age-locked generic design), Pure (age 7 design — memory; age 15 design — present), Marcus (age-locked generic design), Earl (memory only), two classmates (extras)
- **Animation states:**
  - Delia: entering (tired), kissing (tender), changing (routine), leaving (resigned)
  - Pure: sleeping, waking, eating, sitting (alone), standing, walking, remembering
  - Marcus: entering (checking), looking (resentful), paying (reluctant care), leaving
  - Earl: kneeling, holding, promising, vanishing (memory only)
- **VFX:** memory transition (wavy/sepia), clock time distortion, gunshot (audio), final silhouette, title card
- **Style note:** Beat 1.14 (Earl's Ghost flashback) gets M2S-referenced period styling — see "Visual Style Reference" above. Earl's wardrobe, the street setting, and staging should read early-90s; the rest of Sequence 1 stays contemporary.
- Full detail: `scenes/sequence_01_setup_breakdown.md`

---

## Sequence 2: The Fall ✅ Beats authored (13 beats, 2:51)

- **Locations:** Santa Ana street corner (period-styled), frame-up street/storefront exterior (period-styled), courtroom (period-styled), prison cell (period-styled), prison library (period-styled), prison exterior gate (period → contemporary pivot point), contemporary office interiors (job interviews), anonymous transitional closing space
- **Characters:** Pure — age 15 design (opening arrest beat only), age 27 design in prison-era wardrobe (frame-up through release), age 27 design in contemporary wardrobe (job-interview beats onward)
- **Animation states:** Pure — cuffed/still (x2, deliberately echoed staging), standing (verdict), sitting (cell stillness), typing (uncertain → confident across the coding montage), closing a notebook, walking (release), sitting (interviews), posture-deflating across the rejection montage, sitting alone (closing beat)
- **Style note:** Entire sequence is M2S-period-styled except the job-interview beats (2.11–2.13), which pivot to contemporary styling exactly at Beat 2.10 (the prison gate) — the style pivot is staged as a deliberate lighting/palette shift, not just a wardrobe swap.
- **Resolved:** the age-15 arrest (Beat 2.01) does get its own brief on-screen beat, staged to visually echo the age-27 arrest later in the sequence (Beat 2.04) — the repetition itself carries meaning, so both got a beat rather than compressing the teen arrest into pure VO.
- **New technique:** repeated-window time-compression device (Beat 2.09) — identical camera framing held across the ten-year span, only the light changes, making years pass without a calendar graphic.
- Full detail: `scenes/sequence_02_the_fall_breakdown.md`

---

## Sequence 3: The App — beats not yet authored

- **Story beats:** Pure builds "No Sand Beach" app, rewrites his background, gets hired, gets the corner office overlooking Newport Beach. App starts erasing real memories. Earl appears as a glitch on-screen warning him.
- **Likely locations:** Home workspace/laptop, corner office (Newport Beach view), abstract "glitch"/UI space for Earl's appearances
- **Characters:** Pure (age 27 design, contemporary wardrobe), Earl (glitch appearance — **confirmed as a full separate design from his Seq 1 memory design**, not a shared/transitioning one)
- **Animation states (anticipated):** Pure — coding intently, triumphant (new office), unsettled/forgetting (glitch reactions); Earl — glitch materialize, speaking, glitch dissolve
- **VFX:** UI/screen glitch effect, memory-erasure visual metaphor (this is a new VFX category beyond Sequence 1's sepia-memory treatment)
- **Style note:** Earl's glitch design is locked — black-and-white, procedurally-generated "choppy" thread-mask pattern (reference: dense scratchy linework, hollow eyes, hands framing the face), built via the same CA engine as the main render style but tuned to a chaotic/non-convergent rule instead of the smooth dissolution rule. Full spec in `RENDER_STYLE.md`.

---

## Sequence 4: The Collapse — beats not yet authored

- **Story beats:** Pure collapses. Hospital scene — Delia's speech ("I saved your body. I didn't save your heart."). Marcus arrives, they reconcile after 20 years of tension. Pure goes home, deletes the app, memories return.
- **Likely locations:** Hospital room, home (app deletion)
- **Characters:** Pure (age 27 design), Delia (age-locked generic design — no visible-aging pass, per user decision), Marcus (age-locked generic design — same)
- **Animation states (anticipated):** Pure — collapsing, lying in hospital bed, listening, deleting app (relief); Delia — holding hand, speaking (raw/vulnerable, different register than Seq 1's tired-tender); Marcus — entering hospital, embracing (first hug in 20 years)
- **Key emotional beat:** the Marcus/Pure hug — likely the sequence's visual and emotional centerpiece, deserves its own beat with a held camera composition

---

## Sequence 5: The Courtroom — beats not yet authored

- **Story beats:** Pure petitions for honest expungement. Judge denies him. Pure's response line: "The law doesn't respect me. But I'm not going to let that break me."
- **Likely locations:** Courtroom (interior)
- **Characters:** Pure (age 27 design), Judge (new minor character — not previously designed), possibly Delia/Marcus in gallery for support
- **Animation states (anticipated):** Pure — standing, speaking (resolve, not defeat), listening to denial; Judge — presiding, delivering ruling
- **New asset needed:** Judge character design (not covered by existing roster)

---

## Sequence 6: The Sand — beats not yet authored

- **Story beats:** Pure brings his family to Huntington Beach, kneels and touches sand for the first time. Starts a free coding class for kids; one kid asks how he made it; Pure's answer ("I didn't make it. I came back.")
- **Likely locations:** Huntington Beach (sand/ocean, first time this location appears in the film), coding classroom
- **Characters:** Pure (age 27 design), Delia, Marcus, one or more student-kid extras
- **Animation states (anticipated):** Pure — kneeling, touching sand (the film's title payoff — deserves careful, unhurried animation), teaching, smiling
- **Note:** this is the visual and thematic payoff of the whole film's title; treat as a priority sequence for polish even if shorter than Sequence 1

---

## Sequence 7: The Lesson — beats not yet authored

- **Story beats:** Closing narration over final imagery — the "love isn't a subscription, it's the sand under your feet" thematic statement. Largely voice-over/narration rather than staged action.
- **Likely locations:** Could reuse Sequence 6's beach imagery, or be a montage of prior locations
- **Characters:** Narration only (adult Pure V.O., matching the narrator voice already used in Sequence 1)
- **Open question (carried from `production_metadata.json`):** should this be a standalone sequence, or folded into Sequence 6 as a closing beat? Given it's narration over imagery rather than new staged action, folding it into Sequence 6 would avoid building a near-empty seventh ScenePlan. Recommend deciding this when Sequence 6's beats are authored.

---

## Cross-Sequence Open Questions (asset budget decisions)

1. ~~**Pure's age variants**~~ — **Resolved:** 3 age designs — age 7 (Earl's Ghost flashback only), age 15 (The Setup + the arrest beat opening Seq 2), age 27 (framing/prison through the rest of the film). The age-27 design needs two wardrobe/environment passes (prison-era for the M2S-styled portion of Seq 2, contemporary for Seq 3 onward) but that's costuming, not a fourth sprite base.
2. ~~**Delia's aging**~~ — **Resolved:** single age-locked, generic design used throughout the entire film. No second visibly-older design for Seq 4+; Sequence 4's emotional weight comes from performance/staging, not a costume-and-lighting or redesign time-jump.
3. ~~**Marcus's aging**~~ — **Resolved:** same as Delia — single age-locked, generic design throughout. Supersedes the earlier early-30s/mid-40s two-design plan.
4. ~~**New characters not in the original roster**~~ — **Resolved:** classmates (Seq 1), Judge (Seq 5), and student-kids (Seq 6) all stay simple/generic — no individual design reference needed, no age-variant or period-styling treatment. Lightweight, single-sequence-only designs.
5. ~~**Earl's "glitch" treatment (Seq 3)**~~ — **Resolved:** a fully separate glitch-state design (not a shared sprite with a VFX overlay), built as a black-and-white CA-choppy thread mask — same underlying CA engine as the main render style, tuned to a chaotic rule instead of smooth dissolution. Full spec: `RENDER_STYLE.md`.

Sequences 2–7 need their own beat-by-beat breakdowns (in the style of Sequence 1) authored before they can become `ScenePlan` resources. That authoring work is not yet scheduled — it's the next planning step after Phase A wraps.
