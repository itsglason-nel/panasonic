Base commit: 0d7b700

# A12 SYNTHESIS (00-summary.md)

## Totals
- Lines of Code: Python: 5262, HTML: 14928, JS: 121, CSS: 2184.
- Routes: 90 (reconciled perfectly via AST and Regex).
- Templates: 13 template files in folder. 10 used by `render_template` and includes.
- `current_user` uses: 44. `session` uses: 8.
- Missing Endpoints: 0 major endpoints. The admin page is highly API driven with 81 unique `fetch` calls.
- Admin page POST forms: 0.

## Top 5 Risks
1. **Wall-Screen Logouts**: A strict token expiry will log out unattended wall screens (like `/scoreboard/line/*` polling on 30s timers).
2. **IP Lockout**: 5 failed attempts locks out the IP for 300s (`auth.py:23`), affecting all 5+ accounts sharing that PC.
3. **Missing Attribution**: DB writes (e.g. `/admin/api/wip-resolve`) do NOT record identity in `linestat` or `worksched` today.
4. **Downloads**: Authenticated file downloads will require token passing in headers and handling Blobs in JS.
5. **State Sync**: Managing local token state if a tab is duplicated.

## What I did NOT check
- I did NOT check what happens at PC or Browser restart, as the code only specifies server-side TTL. Browser behavior is client-specific.
- I did NOT run the app or check runtime dynamic routes.

## Open Questions for Owner
1. **Network**: What address do people type on the LAN? (Assume: `http://<LAN_IP>:8080`)
2. **Browsers**: What browsers are used on the PCs? Are tabs restored at startup? (Assume: Chrome/Edge, tabs restored)
3. **Wall screens**: Which pages exactly? Are they dedicated accounts? (Assume: `/dashboard` and `/scoreboard`, dedicated read-only accounts)
4. **Traceability**: Do you need to know who did what in `linestat`? (Assume: Yes)
