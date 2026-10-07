Base commit: 0d7b700

# A0 PROJECT FACT SHEET

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
