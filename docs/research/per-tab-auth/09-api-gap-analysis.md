Base commit: 0d7b700

# A9 DATA AND API GAP ANALYSIS

- **Dashboard**: Needs JSON API for `linestat` and `worksched` data.
  - Existing endpoint: `GET /api/dashboard/data`.
- **Admin**: Heavily server-rendered.
  - Missing endpoints: Almost all forms submit via standard POST. Requires massive rewrite to convert to JSON APIs for Shell pages.
- **Pilot Page Recommendation**: The `Scoreboard` or `Dashboard`. It has minimal interaction (read-only) and is already somewhat decoupled.
