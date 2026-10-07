Base commit: 0d7b700

# A9 DATA AND API GAP ANALYSIS
- The Admin page is already extremely API-driven, contrary to my previous report. It utilizes 81 `fetch()` calls in `scripts.html` to load modules, tags, areas, users, etc.
- **Pilot Page Recommendation**: The `Scoreboard` (`line.html`) because it only has 2 fetch calls (`/api/scoreboard/data` and `/api/scoreboard/logs`) and is heavily isolated from state-mutating API calls.
