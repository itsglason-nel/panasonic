# Session Hardening Research

## Versions
- Flask==3.1.1
- Flask-Login==0.6.3
- Flask-Session==0.8.0

## Codebase Audit
a. **Usage of auth constructs**:
   - `session`, `session_ext`, `login_manager`, `before_request`, `after_request` are initialized and heavily used in `app/__init__.py`.
   - Redis is used for Flask-Session.
   - `current_user` is widely used in templates to display `current_user.username`, `full_name`, and `role`.
   - `SECRET_KEY` is loaded in `config.py` from the environment.
b. **Login/Logout**:
   - Login uses standard form POST to `/auth/login`, validates CSRF, uses `login_user(user)`, and redirects.
   - Logout is a GET link to `/auth/logout`, calls `logout_user()`, and redirects.
c. **fetch/XHR calls**:
   - Around 40+ `fetch()` calls located mostly in `app/templates/admin/components/scripts.html` and other templates.
   - `window.fetch` is already wrapped in `scripts.html` to intercept 401s and 302 redirects to `/auth/login`. We must *extend* this existing wrapper rather than replace it.
d. **Server-rendered HTML vs JSON**:
   - The app heavily relies on server-rendered HTML pages that embed user data directly (e.g., `{{ current_user.full_name }}`).
e. **Static routes / Downloads**:
   - Serves static files from `static_folder='static'`.

## Decision on Server-Rendered Pages
**Analysis**: Browser page navigations (Back/Forward, address bar) don't carry an `Authorization` header, so they fall back to the session cookie. This creates a mismatch risk if per-tab tokens are used.
**Decision**: We will rely on browser host isolation (e.g., `localhost` vs `127.0.0.1`) instead of per-tab tokens to handle multiple concurrent user sessions without breaking server-rendered templates. Per-tab tokens (and the associated `<meta>` tag mismatch check) are DEFERRED.

## Library Findings
- **Flask-Login (0.6.3)**: 
  - *Load Order & `current_user` caching*: By reading the installed 0.6.3 source code, `current_user` proxies to `_get_user()`, which caches the user on `flask.g._login_user`. Crucially, `LoginManager._load_user()` checks the session *first*. If a session cookie exists, it never calls `request_loader`. Therefore, to make the token override the cookie, we MUST use a `before_request` hook to decode the token and manually set `flask.g._login_user = user`. This completely bypasses the cookie loading.
  - *Login Action*: Never call `login_user()` for token requests, as it writes the user ID to the session cookie.
  - *Session Protection*: `basic` only marks the session not fresh and never logs out; `strong` clears non-permanent sessions (mine).
  - *Idle Timeout*: The server-side TTL acts as an idle timeout (unverified until B2 is done).
  - *Sources*: [Flask-Login 0.6.x Source Code - `_get_user`](https://github.com/maxcountryman/flask-login/blob/0.6.3/flask_login/utils.py#L26), [Flask-Login 0.6.x Source Code - `_load_user`](https://github.com/maxcountryman/flask-login/blob/0.6.3/flask_login/login_manager.py#L329)
- **Flask-Session (0.8.0) & Flask (3.1.1)**:
  - *Config*: Uses `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`.
  - *Sources*: [Flask Session configuration](https://flask.palletsprojects.com/en/3.1.x/config/#SESSION_COOKIE_HTTPONLY)
- **Cache-Control, bfcache & Vary**:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` prevents bfcache. However, some aggressive browsers may ignore it. A fallback is a `pageshow` event listener: if `event.persisted` is true, force `location.reload()`.
  - When modifying the `Vary` header (e.g., `Vary: Cookie, Authorization`), we must append to it rather than overwriting existing values.
  - *Sources*: [MDN Web Docs Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control), [MDN Web Docs bfcache](https://web.dev/articles/bfcache)
- **Logout GET Requests**:
  - Since logout is a simple GET link (`<a href="/auth/logout">`), we must intercept the click in JS to clear the token from `sessionStorage` before the browser navigates away, or clear the token universally when the login page loads.
- **CSRF with Fetch POSTs**:
  - The API blueprints are already exempted from CSRF in `app/__init__.py`. If we add token auth to them, CSRF is naturally mitigated (tokens aren't automatically sent by the browser like cookies).

## Recommended Order
1. Cache-Control Header Hardening (Phase 2)
2. Cookie Hardening (Phase 3)
   - **Env Vars**: `HARDEN_API_CACHE` (default ON), `REQUIRE_HTTPS` (default OFF). Accepted values: 1/true/yes/on for True, 0/false/no/off for False.
   - **Rollback**: To rollback, unset the `REQUIRE_HTTPS` env var and restart the server, or run `git revert c95a893` with a normal push.
   - **Expected Baseline**: Cookie `session` must show HttpOnly checked, Path=/, SameSite=Lax, Secure unchecked. (Setting REQUIRE_HTTPS=True turns on Secure, which would log everyone out over plain HTTP).
3. Per-Tab Tokens (Phase 4 - DEFERRED)
4. Phase 5: Verification and Cleanup
   - Verify test users are gone.
   - Flush test sessions.

## DECISION GATE: Server-Rendered Data
**Count of templates rendering user data**: 5 (`dashboard.html`, `base.html`, `admin.html`, `admin/components/scripts.html`, `admin/components/modals.html`).
**Count of routes**: Multiple core routes across `admin.py`, `auth.py`, and `api.py` rely on server-side rendering or `current_user` variables directly injected into HTML.

**Recommendation on Phase 4 (Per-Tab Tokens)**:
Due to the heavy reliance on server-side rendering of user data, skipping Phase 4 is confirmed. 

**Alternative (Selected)**: Use browser host isolation (e.g., `localhost` vs `127.0.0.1`). Browsers natively isolate cookies by host. This achieves perfect per-tab/per-window isolation without any code changes, completely avoiding the complexities of JWTs, mismatch checks, and XSS risks.

## Phase 2 Findings
- The application's `after_request` hook now conditionally applies strict `Cache-Control` (`no-store, no-cache, must-revalidate, max-age=0`), `Pragma: no-cache`, and `Expires: 0` headers to both `text/html` and `application/json` responses.
- The `Vary` header is dynamically appended with `Cookie` without overwriting existing `Vary` values.
- Static assets (`/static`) are explicitly bypassed.
- This API cache hardening behavior can be disabled in the environment by setting `HARDEN_API_CACHE=False`.

### Risks Noted
- **Silent Session Fallback**: In `app/__init__.py` (lines 47-61), if Redis connection fails on startup, the application silently catches the exception and falls back to `filesystem` sessions (`app/.flask_sessions/`). This means horizontal scaling or multi-process deployments could suffer from split-brain sessions without any immediate error being thrown.
- **Live Database & Config**: Both `DevelopmentConfig` and `ProductionConfig` use the identical `plcdata` MySQL database URI. Test users (ids 4 and 5) were created directly in the live database during previous script runs.
- **Startup Side Effects**: Calling `create_app('development')` triggers live side effects: it runs `db.create_all()`, updates the `linestat` table (`UPDATE linestat SET updtime = NOW()`), and starts three background observer threads.
- **Test-User Deletion Record**: Test users 4 and 5 (`test_user_a`, `test_user_b`) were manually deleted using a plain PyMySQL script (`DELETE FROM users WHERE id IN (4, 5)`), and their corresponding session files were flushed from `.flask_sessions`.
