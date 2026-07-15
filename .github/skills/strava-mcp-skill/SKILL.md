---
name: strava-mcp
description: Access Strava data — activities, segments, routes, athlete profile, training stats, and workout analysis — through the strava MCP server. Use when the user asks about Strava activities, workouts, rides, runs, training load, fitness trends, heart-rate/power zones, segment efforts, routes, GPX/TCX exports, or to connect/disconnect their Strava account.
---

# Strava MCP

Talk to Strava data through the local `strava` MCP server (npm: `@r-huijts/strava-mcp-server`). The server runs over stdio and auto-loads credentials from `~/.config/strava-mcp/config.json`, so no env vars are needed.

## Prerequisites

- `strava-mcp-server` on PATH (verify with `which strava-mcp-server`).
- Credentials at `~/.config/strava-mcp/config.json` (clientId, clientSecret, accessToken, refreshToken).
- The `strava` MCP must be registered in `opencode.json` under `mcp.strava` with `type: "local"`, `command: ["strava-mcp-server"]`, `enabled: true`.

## Invoking tools

Call MCP tools through the `skill_mcp` tool, using `mcp_name="strava"` and the raw tool name:

```
skill_mcp(mcp_name="strava", tool_name="get-athlete-stats")
```

Some clients also expose the tools directly with a `strava_` prefix (e.g. `strava_get-athlete-stats`). Use whichever the environment offers.

## Connection management

Run these first if the session's first Strava request fails — tokens may be expired.

| Tool | Purpose |
|---|---|
| `check-strava-connection` | Verify the account is connected and tokens are valid. Call this before any data request. |
| `connect-strava` | Re-authenticate (opens a browser OAuth flow). Pass `force: true` to reconnect. |
| `disconnect-strava` | Clear locally stored credentials. |

## Available tools (24)

### Activities (6)
- `get-recent-activities` — most recent activities (pagination via `per_page`, `page`).
- `get-all-activities` — full activity history (slower; prefer `get-recent-activities` for "this week/month" questions).
- `get-activity-details` — single activity: distance, time, speed, calories, gear. Requires `activityId`.
- `get-activity-streams` — second-by-second data: power, heart rate, cadence, velocity, latlng, time. Requires `activityId` + `streamTypes` (default usually sufficient).
- `get-activity-laps` — lap splits for an activity (intervals, rests).
- `get-activity-photos` — photos attached to an activity (requires `activityId`).

### Athlete (4)
- `get-athlete-profile` — the authenticated athlete's profile (weight, FTP, clubs).
- `get-athlete-stats` — cumulative totals (recent ride/run achievements, biggest climb, distance totals). Default time window: recent 4 weeks + year totals.
- `get-athlete-zones` — configured heart-rate and power zones (needed for time-in-zone analysis).
- `list-athlete-clubs` — clubs the athlete belongs to.

### Segments (6)
- `get-segment` — segment metadata (distance, avg grade, climb category). Requires `segmentId`.
- `explore-segments` — find popular segments in a bounding box (`bounds: [sw_lat, sw_lng, ne_lat, ne_lng]`) or near a point. `activityType` optional (default: riding).
- `list-starredSegments` — the athlete's starred segments.
- `star-segment` — star a segment (`segmentId`, `starred: true/false`).
- `get-segment-effort` — a single effort on a segment (`effortId`).
- `list-segment-efforts` — the athlete's efforts on a segment (`segmentId`, pagination).

### Routes (4)
- `list-athlete-routes` — routes created by the athlete (`athleteId`, pagination).
- `get-route` — route geometry + metadata (`routeId`). Useful for GPX/TCX export prep.
- `export-route-gpx` — download a route as GPX (`routeId`); returns file content.
- `export-route-tcx` — download a route as TCX (`routeId`).

### Meta (1)
- `get-server-version` — strava-mcp-server version. Useful for diagnostics, not coaching work.

## Common workflows

### Analyze a recent workout
1. `get-recent-activities` → pick the target activity ID.
2. `get-activity-details` for headline stats.
3. `get-activity-streams` with `streamTypes: ["time", "heartrate", "watts", "cadence", "velocity_smooth"]` for deep analysis.
4. `get-activity-laps` for interval splits.
5. Cross-reference with `get-athlete-zones` to compute time-in-zone.

### Weekly/monthly summary
1. `get-recent-activities` with enough `per_page` to cover the window (or `get-all-activities` paginated).
2. Aggregate distance, time, elevation per activity type.
3. Compare with `get-athlete-stats` for year-to-date context.

### Segment scouting
1. `explore-segments` with the area's bounding box (or `list-starred-segments` for the athlete's saved ones).
2. `get-segment` for the candidate's full profile.
3. `list-segment-efforts` to see the athlete's history on it.

### Route export
1. `list-athlete-routes` to find the route ID.
2. `get-route` to confirm it's the right one.
3. `export-route-gpx` or `export-route-tcx` to pull the file.

## Best practices

- **Always check connection first** — call `check-strava-connection` before data requests if there's any chance tokens expired (tokens last ~6 hours; the server auto-refreshes, but a fresh session can fail if the stored refresh token is invalid).
- **Prefer `get-recent-activities` over `get-all-activities`** for "this week/month" questions — the latter scans the entire history and is slow.
- **Pagination** — most list tools take `per_page` (max 200 for activities, 200 for segments) and `page` (1-indexed).
- **Rate limits** — Strava allows ~100 requests / 15 min / athlete, 1000 / day. Chunk multi-activity analysis and cache `get-activity-details` / streams results within the turn rather than re-fetching.
- **Zones are per-athlete config**, not per-activity — fetch once per session and reuse for time-in-zone calculations.
- **Stream keys** — common `streamTypes`: `time`, `distance`, `latlng`, `velocity_smooth`, `heartrate`, `watts`, `watts_avg`, `cadence`, `grade_smooth`, `altitude`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Unauthorized` / 401 on any request | Call `connect-strava` (with `force: true` if needed); retry. |
| `Record not found` on `get-activity-details` | Check the `activityId` came from the same athlete and isn't a privacy-redacted one. |
| `get-activity-streams` returns subsets of requested types | Some activity types lack streams (e.g. manual entries) — verify the activity was GPS-tracked. |
| Slow startup / `strava` MCP not listed | Verify `strava-mcp-server` is on PATH and `mcp.strava.enabled` is `true` in opencode.json. Run `strava-mcp-server` once manually to surface startup errors. |