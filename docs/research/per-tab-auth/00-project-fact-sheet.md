Base commit: 0d7b700

# A0 PROJECT FACT SHEET
1. Pages: /auth/login (Public), /admin (Logged In), /dashboard (Wall-screen), /scoreboard/line/<lineno> (Wall-screen). VERIFIED.
2. Polling: line.html:502 uses setInterval(fetchProdData, 30000), line.html:503 uses setInterval(fetchLogsData, 30000). all_lines.html:184 uses setInterval(updateScoreboard, 10000). scripts.html:362 uses setInterval for schedules (30s). scripts.html:5860 uses setInterval for scoreboard (10s). VERIFIED.
3. Dashboard on 401: Redirects to /auth/login. Unattended screens get stuck. VERIFIED.
4. Accounts: Created via UI or alter_db.py. Lockout is IP-based, module-level dict. password rules: unknown. is_active: checked in login_required. VERIFIED.
5. Writes: 33 routes write data. NONE store identity. VERIFIED.
6. Session behaviour: PC/Browser restart: UNKNOWN (client specific).
7. Front-end stack: HTML (14928 lines), Python (5262 lines), JS (121 lines), CSS (2184 lines). VERIFIED.
8. Deployment: waitress-serve on 0.0.0.0. VERIFIED.
9. Tests: None. VERIFIED.
10. Startup side effects: plc_observer threads start. VERIFIED.
11. Weaknesses: IP-based lockout affects all accounts on shared PC.
