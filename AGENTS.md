# AGENTS.md — strava_fitness_coach

## Local skills

Project-specific skills live in `.github/skills/` (not the global agent-specific skills directory). This keeps them tool-agnostic and version-controlled with the repo — any agent or CI that follows the `SKILL.md` convention can use them.

Installed local skills:
- `.github/skills/strava-gym-analysis/` — analyze Strava gym sessions and regenerate `GYM_PROGRAM.md` aligned to `TRAINING_PLAN.md`. Triggered by "analyze my gym data", "refresh my gym program", "toned/curvy", "Hyox strength prep", etc.

## Project layout

- `TRAINING_PLAN.md` — periodised run + race plan (Jul 2026 → Apr 2027). Source of truth for weekly skeleton, race targets, phase dates. Gym work is downstream of this.
- `GYM_PROGRAM.md` — gym strength program, aligned to the phases in `TRAINING_PLAN.md`. Goals: toned/curvy physique (glute hypertrophy) + Hyrox-ready strength. Regenerate via the `strava-gym-analysis` skill.
- `opencode.json` — registers the local `strava` MCP server (`strava-mcp-server` on PATH). MCP loads only at startup, so config changes need a restart.

## Working conventions

- **Always read `TRAINING_PLAN.md` before touching `GYM_PROGRAM.md`** — the gym program is downstream of the run plan and must not violate its weekly skeleton or deload weeks.
- **Strava gym data lives in the activity `description` field** (populated by Hevy or Lyfta) — `strava_get-activity-details` surfaces it. Streams are not useful for gym activities; only HR is worth pulling.
- **Athlete context is in `ctx_memory`** (CONFIG_VALUES id 11): Gabriella, Singapore, athlete ID 118273162, physique goal + Hyrox Apr 2027. Reference it rather than re-asking.
- **Memory tool can error intermittently** — retry once, then skip silently if it still fails. The on-disk files (`TRAINING_PLAN.md`, `GYM_PROGRAM.md`) are the source of truth, not memory.

## Repo conventions

- No emojis in generated docs unless the user asks.
- Markdown files at the project root for human-facing plans; skills and tooling under `.github/`.
- Conventional Commits style if committing.