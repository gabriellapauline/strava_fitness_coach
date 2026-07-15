---
name: strava-training-plan
description: Generate a running performance analysis and race-targeted training plan from Strava history. Use when the user asks to "regenerate my training plan", "analyze my running", "plan for 10km/half marathon/Hyrox", "refresh TRAINING_PLAN.md", or mentions race targets and wants a structured schedule. Produces a TRAINING_PLAN.md in the project root.
---

# Strava Training Plan Generator

End-to-end pipeline: pull Strava run history → aggregate by month → compare HR/effort at matched distances → write a phase-based training plan for the user's stated race targets. Output goes to `TRAINING_PLAN.md` in the project root.

## Prerequisites

- `strava` MCP server registered and connected (see strava-mcp skill). If any data fetch returns 401, call `connect-strava` with `force: true` and retry.
- Python 3 on PATH (used only for aggregation math; no packages required).

## Workflow

### 1. Gather race targets and constraints

Ask the user (only if not already stated in the session):
- Race 1: distance + date
- Race 2 (optional): distance + date
- Race 3 (optional): distance + date
- Weekly availability: how many runs? gym sessions? pilates/yoga? other fixed sessions?

Save targets to `ctx_memory` under CONFIG_VALUES so future sessions inherit them (see memory id 11 for the canonical format).

### 2. Fetch Strava data

Call in parallel where possible (watch rate limits — 100 req / 15 min):
- `strava_get-athlete-profile`
- `strava_get-all-activities` with `endDate` = today, `maxActivities` 500, `perPage` 200, `maxApiCalls` 5
- `strava_get-athlete-zones`

Filter the activity list down to type "Run". Skip sub-1km warm-up uploads (or note them as noise — they drag pace aggregates).

### 3. Aggregate and analyze

Run the bundled script:

```bash
python3 ~/.config/opencode/skills/strava-training-plan/scripts/analyze.py <csv_path>
```

Build the CSV from the activity list first (columns: `date,distance_km,duration_sec,indoor` — indoor = 1 for treadmill, 0 for outdoor). See `analyze.py` for the expected format and the metrics it computes:
- Monthly: run count, total km, avg km, avg pace, indoor %, longest run
- 6-month window: first-half vs second-half totals, long-run count, weekly frequency
- Baseline (oldest 2 months) vs recent 6 months
- Longest run per month (endurance progression)

### 4. Effort comparison (optional but high-value)

Pick two runs of similar distance, ~4–6 months apart, ideally outdoor. Pull HR streams for both:

```
strava_get-activity-streams(id, types=["time","distance","heartrate","velocity_smooth"], resolution="medium", format="compact")
```

Compare avg HR, max HR, pace — using zones from step 2. This surfaces cardiovascular efficiency gains that monthly pace aggregates hide (a flat pace at lower HR = real fitness improvement).

### 5. Generate the plan

Write `TRAINING_PLAN.md` with these sections (see existing `/Users/gabriella/Git/strava_fitness_coach/TRAINING_PLAN.md` for the canonical template — mimic its structure):

1. **Header** — athlete name, constraints, all race targets with dates.
2. **Baseline** — current easy pace, long run distance, run frequency, gym/pilates cadence, HR zones.
3. **Weekly skeleton** — generic template (Mon gym / Tue quality run / Wed pilates / Thu easy / Fri rest / weekend long).
4. **Phase per race** — one phase block per target, each with:
   - Phase name + date range + week count
   - Race targets (A/B/C time goals)
   - Weekly table (week #, dates, quality run, long run, optional easy)
   - Include deload weeks every 3–4 weeks
   - Include a taper week ending on race day
5. **Phase transitions** — note recovery between phases, pivots (e.g., Hyrox shifts run→gym emphasis).
6. **Two baseline-improvement tips** — custom HR zones; warm-up-upload hygiene.
7. **Race-day pacing notes** — per race, first/middle/last segment paces and target finish.

### 6. Save and confirm

After writing `TRAINING_PLAN.md`, print a 3–4 line summary of what changed since last generation (new activities incorporated, plan shifted, etc.) and remind the user the plan is at `TRAINING_PLAN.md`.

## Customization hooks

- **Race targets change** → update memory id 11 + rerun this skill.
- **New race added** → ask date + distance, insert a new phase block before the next one, adjust dates downstream.
- **Only want the analysis (no plan)** → run steps 1–4 only, output to chat, skip the file write.
- **Want a calendar file** → after writing the .md, offer to generate a `.ics` from the weekly tables.

## Key principles baked into the plan

- **Long run is the #1 predictor** for endurance events — progress it gradually (~10% / week), deload every 3–4 weeks.
- **Quality run is the #1 predictor for speed** — intervals or tempo once a week, never both at high dose.
- **Third weekly run is optional** — only if the athlete is fresh; skip when fatigued. Consistency > volume.
- **Cross-training counts** — gym and pilates are real training load; don't schedule hard runs adjacent to hard gym days.
- **Hyrox pivots the emphasis** — running drops to maintenance, gym goes Hyrox-specific (sled, wall balls, farmer's carry, burpees, rowing), station technique > more running.

## Common pitfalls (avoid these)

- Monthly avg pace can be misleading: long slow runs and short warm-up uploads smear the signal. Always cross-check with a matched-distance HR comparison.
- Strava default HR zones are age-based, not lab-tested — flag this and recommend a 20-min max-effort test to set custom zones.
- Rate limits bite when fetching streams for many activities — cache results within the turn, fetch at most 2–3 stream sets per run.
- Taper weeks are not rest weeks — volume drops ~30–40%, intensity stays (short strides keep the legs snappy).