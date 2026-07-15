---
name: strava-gym-analysis
description: Analyze Strava gym/strength sessions and regenerate a physique- and Hyrox-aligned gym program. Use when the user asks to "analyze my gym data", "refresh my gym program", "update my gym routine", "what exercises should I do in the gym", mentions toned/curvy physique goals or Hyrox strength prep, or wants to update GYM_PROGRAM.md. Produces/updates GYM_PROGRAM.md in the project root.
---

# Strava Gym Analysis & Program Generator

End-to-end pipeline: pull Strava gym/strength sessions → extract exercise inventory and loads → identify gaps vs stated physique goals + Hyrox prep → write or update `GYM_PROGRAM.md` aligned to the periodisation in `TRAINING_PLAN.md`.

## Prerequisites

- `strava` MCP server registered and connected (see strava-mcp skill). If any data fetch returns 401, call `connect-strava` with `force: true` and retry.
- Read `TRAINING_PLAN.md` and (if present) `GYM_PROGRAM.md` at the project root first — the gym program is *downstream* of the run plan and must stay aligned to its phases.

## Athlete context (canonical)

 Gabriella Pauline Djojosaputro — Singapore, athlete ID 118273162.
- **Physique goal:** toned and curvy (glute/hip hypertrophy is the #1 driver).
- **Hyrox:** early April 2027 — needs sled push/pull, wall balls, sandbag lunges, farmers carry, burpees, rowing.
- **Constraints:** gym 1–2×/wk (Phases 1–2), 2–3×/wk (Phase 3 Hyrox). Always leave legs fresh for quality/long runs.
- **Current baselines + progression targets:** see the "Strength levels" table at the top of `GYM_PROGRAM.md` — edit that table rather than this skill file when loads change.

## Workflow

### 1. Read the run plan + existing gym program

Read `TRAINING_PLAN.md` for the active phase, race targets, weekly skeleton (Mon gym / Tue quality run / Wed pilates / Thu easy / Fri rest-or-gym / weekend long run), and phase transitions. Read `GYM_PROGRAM.md` if it exists, to diff against the new output.

### 2. Fetch Strava gym sessions

Use `strava_get-recent-activities` with `per_page=50` first; expand to `get-all-activities` if the window is too short. Filter the list to `type == "WeightTraining"` (Strava names: "Strength", "Full Body", "Back", "Evening workout 🏋️", etc.). Note moving time and, when present, avg/max HR and calories.

### 3. Extract exercise inventory

Call `strava_get-activity-details` for each gym activity. Hevy/Lyfta logs put the exercise list in the **description** field — parse sets, reps, and loads from there. Use a generous concurrency (e.g. 6–8 in parallel) but stay under the 100 req / 15 min Strava limit. Skip duplicate-fetches of the same activity within a turn.

Aggregate into a frequency table:
- **Every session** — exercises in >80% of sessions (anchor lifts)
- **Very frequent** — 50–80%
- **Frequent** — 25–50%
- **Occasional** — <25%

Record current best loads (heaviest set × top reps) per lift — these become the "strength levels" table.

### 4. Identify gaps vs goals

Compare the observed inventory against what the two goals require:

**Curvy/toned (glute/hip hypertrophy) requires:**
- Hip thrust (barbell) — the #1 glute lift; almost mandatory
- Squat pattern (goblet → front squat) — quad + glute
- RDL (anchor — posterior chain)
- Walking lunges / Bulgarian split squat — glute med + max
- Hip abduction (machine or cable) — glute med shape

**Hyrox (early Apr 2027) requires:**
- Wall ball (race weight 6 kg for women)
- Sled push + sled pull
- Sandbag walking lunges (15–20 kg)
- Farmers carry (heavy)
- Burpee broad jumps
- Rowing erg intervals
- Core / anti-rotation (Pallof, hollow holds)

Flag any of these that are **absent** or **under-dosed** (load far below race weight, or appearing in <25% of sessions). These become the "gaps" section.

### 5. Generate the program

Write `GYM_PROGRAM.md` in the project root with this structure (mimic the existing file — see `/Users/gabriella/Git/strava_fitness_coach/GYM_PROGRAM.md` for the canonical template):

1. **Header** — athlete, goal, frequency, companion doc reference.
2. **Current gym baseline** — strength levels table (lift / current / target by end of phase) + observed-pattern notes + gaps list.
3. **Program structure** — weekly layout for Phase 1–2 (2×/wk) and Phase 3 (2–3×/wk), aligned to `TRAINING_PLAN.md`'s weekly skeleton.
4. **Phase 1 & 2 — Build the curves + general strength** — two sessions (A: lower/glutes "curvy day"; B: upper pull/push + Hyrox seeds). Each session: ordered exercise list table (# / exercise / sets×reps / load progression / why). Include progression rules (add 2.5 kg when top reps hit clean for 2 sessions) and deload rules (drop 15–20% on run-plan deload weeks).
5. **Phase 3 — Hyrox specificity + curves maintenance** — H1 base strength / H2 capacity / H3 race-specific, each with session tables. **Critical:** keep a "curves maintenance block" (hip thrust + goblet squat + hip abduction) in the Friday session so the aesthetic goal doesn't regress during Hyrox prep.
6. **The one change that matters most** — single highest-ROI recommendation, called out clearly.

### 6. Confirm and offer memory update

After writing the file, print a 3–4 line summary of what changed since last generation (new activities, new loads, shifted recommendations). Update the `CONFIG_VALUES` memory for the athlete's current strength levels if the numbers moved materially (the memory tool errors intermittently — retry once, then skip silently if it still fails; the file write is the source of truth).

## Triggering keywords

"analyze my gym data", "refresh my gym program", "update gym routine", "what exercises should I do", "toned and curvy", "Hyox strength prep", "gym program" — when in doubt, load this skill.

## Key principles baked into the program

- **Hip thrust is the #1 glute hypertrophy lift** — always present on the lower-body day, first in order, progressive overload weekly.
- **Squat pattern must be present** — goblet squat is the entry point; transition to front squat once 30 kg goblet for 10 is easy.
- **Phase 3 does NOT drop the aesthetic work** — Hyrox specificity + a curves maintenance block on the same day. Both goals coexist.
- **Gym is downstream of running** — never schedule a heavy leg day before a quality run or long run. The Monday/Friday gym slots in the run-plan skeleton are chosen for this reason. Preserve them.
- **Deload weeks are shared** — on run-plan deload weeks (e.g., Wk 4, 12, 16, 20), gym also deloads 15–20% and drops the last set of each lift. Hip thrust and face pulls tolerate the light work and keep the pattern intact.
- **Hyrox seeds start in Phase 1** — wall ball and farmers carry appear as accessories in Session B even during the 10 km block, so technique is familiar before Phase 3.

## Common pitfalls (avoid these)

- **Treating Strava "Strength" activities as opaque** — most of the real data (exercise, sets, reps, load) is in the `description` field, populated by Hevy or Lyfta. `get-activity-details` surfaces it. Parse the description, don't just rely on moving time.
- **Over-fetching streams** — gym activities don't have useful movement streams; skip `get-activity-streams` for them. Only HR (already in details) is worth pulling.
- **Ignoring the run plan** — a gym program that conflicts with the periodisation (e.g., heavy squats the day before a 20 km long run) will fail. Always read `TRAINING_PLAN.md` first.
- **Recommending many new lifts at once** — the athlete is on 1–2 gym days/wk. Adding 5 new exercises in a session destroys adherence. Add at most 2–3 new lifts per session per regeneration, and clearly mark them as **NEW**.
- **Forgetting the aesthetic goal during Hyrox** — it is easy to let the physique goal regress under race-specific load. The Friday curves maintenance block is non-negotiable in Phase 3.
- **Mis-naming the output file** — always `GYM_PROGRAM.md` at the project root, not `GYM.md` or `STRENGTH.md`.