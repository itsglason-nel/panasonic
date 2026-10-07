Base commit: 0d7b700

# A0 PROJECT FACT SHEET

## 1. Pages
- `/auth/login` (auth): Public. Purpose: Login.
- `/admin` (admin): Logged In. Purpose: General management.
- `/dashboard` (admin): Operator. Purpose: Wall-screen (auto-refreshing read-only).
- `/scoreboard/line/<lineno>` (scoreboard): Operator. Purpose: Wall-screen scoreboard.

## 2. Polling
- `app/templates/scoreboard/line.html:502`: `setInterval(fetchProdData, 30000)` (30 seconds). Endpoint: `/api/scoreboard/data`
- `app/templates/scoreboard/line.html:503`: `setInterval(fetchLogsData, 30000)` (30 seconds). Endpoint: `/api/scoreboard/logs`
- *No `<meta http-equiv="refresh">` tags found in any templates.*

## 3. Dashboard on 401
- VERIFIED: redirects to `/auth/login` (unattended screens get stuck on login page).

## 4. Accounts
- **Creation**: UI or `tools/alter_db.py`.
- **Lockout**: IP-based (`_login_attempts[ip]`).
- **Counts per role**: [PENDING OWNER RESULT]

## 5. Actions that write data
- `/admin/api/wip-resolve` writes to `linestat`. NO identity column.
- `/admin/api/trigger-pdf` writes to `models`. NO identity column.
- `tools/alter_db.py` writes to `users` and `models`. NO identity column.

## 6. Session behaviour today
- **Browser restart**: UNKNOWN (Depends on browser configuration if tabs are restored).
- **PC restart**: UNKNOWN.

## 7. Front-end stack
- HTML: 14,928 lines. Python: 5,262 lines. JS: 121 lines. CSS: 2,184 lines.

## 8. Deployment
- `waitress-serve` on `0.0.0.0:8080`.

## 9. Tests
- No unit test suite exists in repo.

## 10. Startup side-effects
- `create_app()` starts background observer threads.

## 11. Weaknesses
- IP-based lockout punishes all users on a shared PC.
