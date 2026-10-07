Base commit: 0d7b700

# A12 SYNTHESIS (00-summary.md)

## Totals
- Routes: 50+
- Templates: 30+
- Missing Endpoints: Major gap in Admin (forms are not API-driven).

## Top 5 Risks
1. **Admin Rewrite**: Moving to Shell pages + API requires rewriting all Admin Jinja forms into JS components.
2. **File Downloads**: Authenticated downloads via token require JS Blob handling, which is complex for large files.
3. **Wall-Screen Logouts**: A strict token expiry will log out unattended wall screens if not refreshed silently.
4. **Third-Party Integrations**: If any undocumented clients exist, requiring a header token will break them.
5. **State Sync**: Managing JWT/token state across multiple tabs during disconnects.

# 12-open-questions.md

## Questions for Owner (Unknowns)
1. **Network**: What address do people type on the LAN? (Assume: `http://<LAN_IP>:8080`)
2. **Browsers**: What browsers are used on the PCs? Are tabs restored at startup? (Assume: Chrome/Edge, tabs restored)
3. **Wall screens**: Which pages exactly? Are they dedicated accounts? (Assume: `/dashboard` and `/scoreboard`, dedicated read-only accounts)
4. **Traceability**: Do you need to know who did what in `linestat`? (Assume: Yes, but schema doesn't support it yet)
