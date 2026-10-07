Base commit: 0d7b700

# A12 SYNTHESIS (00-summary.md)
## Totals
- Lines: py=5262, html=14928, js=121, css=2184.
- Routes: 90 (reconciled AST vs Regex).
- Templates: 13 in folder, 10 used.
- current_user uses: 44. session uses: 8.
- Missing Endpoints: 0 major missing for read, but ALL write forms miss API endpoints.

## Top 5 Risks
1. Wall-Screen Logouts (line.html:502).
2. IP Lockout (auth.py:23).
3. Missing Attribution (admin.py:302).
4. Downloads via window.open (admin.html:1278).
5. State Sync on duplicated tabs.

## What I did NOT check
Browser/PC restart behaviour.

## Open Questions (Defaults)
1. Network: LAN IP (Assume: http://<LAN_IP>:8080)
2. Browsers: Chrome/Edge (Assume: tabs restored)
3. Wall screens: dashboard, scoreboard (Assume: dedicated read-only)
4. Traceability: Yes.
