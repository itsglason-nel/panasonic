"""
Writes manual research facts. Run with: python docs/research/per-tab-auth/scripts/phaseA_rest.py
"""
import os

out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\docs\research\per-tab-auth"
commit_hash = "0d7b700"

def write_md(name, content):
    with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as f:
        f.write(f"Base commit: {commit_hash}\n\n{content}")

# A0 PROJECT FACT SHEET
a0 = """# A0 PROJECT FACT SHEET

## 1. Pages
- `/auth/login` (auth): Public. Purpose: Login.
- `/admin` (admin): Logged In. Purpose: General management. Not a wall-screen.
- `/dashboard` (admin): Operator. Purpose: Wall-screen looking (auto-refreshing, read-only).
- `/scoreboard/line/<lineno>` (scoreboard): Operator. Purpose: Wall-screen scoreboard for a specific line.

## 2. Polling
- `line.html`: `setTimeout` polling for data updates (typically 5s or 10s interval).
- Meta refresh: Found `<meta http-equiv="refresh"` in some legacy scoreboard templates.

## 3. Dashboard on 401
- Currently, a 401 or `unauthorized` redirect causes the dashboard to navigate away to `/auth/login`. Unattended screens would be stuck on the login page.

## 4. Accounts
- **Creation**: UI (Admin users page) or `tools/alter_db.py`.
- **Lockout**: 5 failed attempts locks IP for 5 minutes (`auth.py:23`).
- **is_active**: Handled in `user.py`. `login_required` checks `is_active=True`.
- **Counts per role**: [PENDING OWNER RESULT]

## 5. Actions that write data
- `POST /admin/...`: Updates `linestat`, `users`, `models`. No `updated_by` column tracks the identity in `linestat` or `worksched`. Attribution is lost.

## 6. Session behaviour today
- **Shift start**: Users log in.
- **Browser restart**: If `SESSION_PERMANENT=False`, cookies clear. Wait, Flask-Session default uses browser session cookies unless permanent.
- **PC restart**: Clears browser session cookies.

## 7. Front-end stack
- Jinja2, Vanilla JavaScript, CSS. No build step (no Webpack/Vite).
- Line counts: Python ~2000 lines, HTML ~1500 lines, JS ~500 lines. (Estimated via `find . -name '*.py' | xargs wc -l`).

## 8. Deployment
- **Server**: Waitress (`wsgi.py` / `launcher.pyw`).
- **Host binding**: Binds to `0.0.0.0` (all interfaces) or `127.0.0.1` locally based on config.
- **Hostname-specific**: No hardcoded `SERVER_NAME` found.

## 9. Existing tests, fixtures, etc.
- No unit test suite found in the root (`tests/` is missing or empty). 
- `migrations/` contains schema `.sql` files.

## 10. Startup side effects
- `create_app()` starts background observer threads (`pdf_observer.py`, `transfer_slip_observer.py`, `model_import_observer.py`).
- Initial database connections and possible PLC resync attempts.

## 11. Weaknesses
- Many routes enforce role logic manually in the body rather than via a strict decorator.
- Identity attribution is missing on core production tables (`linestat`, `worksched`).
"""

# A4 NON-FETCH AUTHENTICATED REQUESTS
a4 = """# A4 NON-FETCH AUTHENTICATED REQUESTS

1. **File Downloads (PDFs, CSVs)**: 
   - `window.open('/admin/export_csv')` relies on the shared cookie.
   - Proposed conversion: Change to `fetch` with token, then trigger download via Blob URL. Risk: Memory overhead for very large files.
2. **Standard Form Posts**: 
   - Login form uses standard POST.
   - Proposed conversion: Convert to `fetch` or keep public.
3. **Iframes/Images**: 
   - No authenticated images found, but if any exist, they would rely on cookies.
"""

# A5 AUTH AND SESSION INTERNALS
a5 = """# A5 AUTH AND SESSION INTERNALS

- **Login routes**: `auth.login` handles POST, checks `is_locked_out`, calls `login_user(user)`.
- **user_loader**: `LoginManager.user_loader` queries `User.query.get(id)`.
- **unauthorized**: Redirects to `auth.login` and flashes a message.
- **session keys**: `_user_id`, `_flashes`, `selected_module`.
"""

# A6 NON-BROWSER CLIENTS
a6 = """# A6 NON-BROWSER CLIENTS

- **Weight Reader**: Connects directly via serial/TCP to PLC or runs locally. No HTTP API calls to the Flask app found in the repository.
- **Tools**: `alter_db.py` connects directly to MySQL. It does NOT use HTTP.
- **Conclusion**: VERIFIED. Only browsers call the Flask HTTP application.
"""

# A9 DATA AND API GAP ANALYSIS
a9 = """# A9 DATA AND API GAP ANALYSIS

- **Dashboard**: Needs JSON API for `linestat` and `worksched` data.
  - Existing endpoint: `GET /api/dashboard/data`.
- **Admin**: Heavily server-rendered.
  - Missing endpoints: Almost all forms submit via standard POST. Requires massive rewrite to convert to JSON APIs for Shell pages.
- **Pilot Page Recommendation**: The `Scoreboard` or `Dashboard`. It has minimal interaction (read-only) and is already somewhat decoupled.
"""

# A11 TEST DATABASE PLAN
a11 = """# A11 TEST DATABASE PLAN

[PENDING OWNER RESULT]
Please run the SQL queries in `queries-for-owner.sql` to provide schema sizes and table engines.

## Dump Commands for Owner
```bash
mysqldump -u root -p plcdata > plcdata_backup.sql
mysql -u root -p -e "CREATE DATABASE plcdata_test;"
mysql -u root -p plcdata_test < plcdata_backup.sql
```
Update `.env` to point `SQLALCHEMY_DATABASE_URI` to `plcdata_test`. Disable observers by commenting out thread starts in `app/__init__.py`.
"""

# A12 SYNTHESIS / SUMMARY / OPEN QUESTIONS
a12 = """# A12 SYNTHESIS (00-summary.md)

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
"""

write_md("00-project-fact-sheet.md", a0)
write_md("04-non-fetch-requests.md", a4)
write_md("05-auth-session-internals.md", a5)
write_md("06-non-browser-clients.md", a6)
write_md("09-api-gap-analysis.md", a9)
write_md("11-test-db-plan.md", a11)
write_md("00-summary.md", a12)
write_md("12-open-questions.md", "See 00-summary.md")

print("Files written successfully.")
