# Session Hardening Research

## Versions
- Flask==3.1.1
- Flask-Login==0.6.3
- Flask-Session==0.8.0
- PyJWT==2.9.0

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
**Analysis**: Browser page navigations (Back/Forward, address bar) don't carry an `Authorization` header, so they fall back to the session cookie. This means if tab 1 is User A and tab 2 is User B, reloading tab 2 will initially render with User A's data (the cookie owner).
**Decision**: Use a client-side mismatch check. The server will embed the cookie's user ID in the HTML using ONE hidden `<meta>` tag:
`{% if current_user.is_authenticated %}<meta name="user-id" content="{{ current_user.id }}">{% endif %}`
This guards against breaking anonymous pages like the login screen. (No CSP header is currently set in the app that would block this).
The JS fetch wrapper will decode the tab's JWT and compare its `sub` claim to the meta tag.
**Mismatch Strategy**: Fail-closed mismatch. Instead of silently reloading or switching identity, the app will fail closed with a blocking notice and explicit choices.

## Library Findings
- **Flask-Login (0.6.3)**: 
  - *Load Order & `current_user` caching*: By reading the installed 0.6.3 source code, `current_user` proxies to `_get_user()`, which caches the user on `flask.g._login_user`. Crucially, `LoginManager._load_user()` checks the session *first*. If a session cookie exists, it never calls `request_loader`. Therefore, to make the token override the cookie, we MUST use a `before_request` hook to decode the token and manually set `flask.g._login_user = user`. This completely bypasses the cookie loading.
  - *Login Action*: Never call `login_user()` for token requests, as it writes the user ID to the session cookie.
  - *Session Protection*: Set via `login_manager.session_protection`. The default behavior is `"basic"`.
  - *Sources*: [Flask-Login 0.6.x Source Code - `_get_user`](https://github.com/maxcountryman/flask-login/blob/0.6.3/flask_login/utils.py#L26), [Flask-Login 0.6.x Source Code - `_load_user`](https://github.com/maxcountryman/flask-login/blob/0.6.3/flask_login/login_manager.py#L329)
- **Flask-Session (0.8.0) & Flask (3.1.1)**:
  - *Config*: Uses `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`.
  - *Sources*: [Flask Session configuration](https://flask.palletsprojects.com/en/3.1.x/config/#SESSION_COOKIE_HTTPONLY)
- **PyJWT (2.9.0)**:
  - *Usage*: Validates `exp` (expiration) and `iat` (issued at).
  - *Sources*: [PyJWT Docs](https://pyjwt.readthedocs.io/en/2.9.0/)
- **Cache-Control, bfcache & Vary**:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` prevents bfcache. However, some aggressive browsers may ignore it. A fallback is a `pageshow` event listener: if `event.persisted` is true, force `location.reload()`.
  - When modifying the `Vary` header (e.g., `Vary: Cookie, Authorization`), we must append to it rather than overwriting existing values.
  - *Sources*: [MDN Web Docs Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control), [MDN Web Docs bfcache](https://web.dev/articles/bfcache)
- **Logout GET Requests**:
  - Since logout is a simple GET link (`<a href="/auth/logout">`), we must intercept the click in JS to clear the token from `sessionStorage` before the browser navigates away, or clear the token universally when the login page loads.
- **CSRF with Fetch POSTs**:
  - The API blueprints are already exempted from CSRF in `app/__init__.py`. If we add token auth to them, CSRF is naturally mitigated (tokens aren't automatically sent by the browser like cookies).

## Token Strategy (Confirmed)
- **Duration**: 30-minute sliding token, capped at an 8-hour absolute maximum.
- **Expiration**: No auto-minting on expiry. Expiry returns a 401, forcing the user to log in again.

## Recommended Order
1. Cache-Control Header Hardening (Phase 2)
2. Cookie Hardening (Phase 3)
3. Per-Tab Tokens (Phase 4)

## DECISION GATE: Server-Rendered Data
**Count of templates rendering user data**: 5 (`dashboard.html`, `base.html`, `admin.html`, `admin/components/scripts.html`, `admin/components/modals.html`).
**Count of routes**: Multiple core routes across `admin.py`, `auth.py`, and `api.py` rely on server-side rendering or `current_user` variables directly injected into HTML.

**Recommendation on Phase 4 (Per-Tab Tokens)**:
Due to the heavy reliance on server-side rendering of user data, skipping Phase 4 is highly recommended. The server will *always* render the initial HTML page with the cookie's user identity. If tab 2 has a token for User B, but the cookie belongs to User A, tab 2 will initially load User A's HTML, trigger the client-side mismatch check, and block the UI. This negates the benefit of per-tab tokens (seamless multi-account usage) because full page navigations will constantly trip the mismatch blocker.

**Alternative**: Use browser host isolation (e.g., `a.localhost` vs `b.localhost`, or different IPs like `127.0.0.1` vs `127.0.0.2`). Browsers natively isolate cookies by host. This achieves perfect per-tab/per-window isolation without any code changes, completely avoiding the complexities of JWTs, mismatch checks, and XSS risks.
