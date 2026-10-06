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
   - `current_user` is widely used in templates (e.g. `base.html`, `dashboard.html`, `admin.html`) to display `current_user.username`, `full_name`, and `role`.
   - `SECRET_KEY` is loaded in `config.py` from the environment.
b. **Login/Logout**:
   - Login uses standard form POST to `/auth/login`, validates CSRF, uses `login_user(user)`, and redirects.
   - Logout is a GET to `/auth/logout`, calls `logout_user()`, and redirects.
c. **fetch/XHR calls**:
   - Around 40+ `fetch()` calls located mostly in `app/templates/admin/components/scripts.html` and other templates.
   - They are same-origin.
   - `window.fetch` is already wrapped in `scripts.html` to intercept 401s and 302 redirects to `/auth/login`. This is the perfect place to inject the `Authorization` header.
d. **Server-rendered HTML vs JSON**:
   - The app heavily relies on server-rendered HTML pages that embed user data directly (e.g., `{{ current_user.full_name }}`).
e. **Static routes / Downloads**:
   - Serves static files from `static_folder='static'`. There are no explicit custom `send_file` downloads that would be affected by cache-control, but we must ensure static assets are not hit with `no-store`.

## Decision on Server-Rendered Pages
**Analysis**: Browser page navigations (Back/Forward, address bar) don't carry an `Authorization` header, so they fall back to the session cookie. This means if tab 1 is User A and tab 2 is User B, reloading tab 2 will initially render with User A's data (the cookie owner), until the JS token overrides API calls.
**Decision**: Use a client-side mismatch check. The server will embed the cookie's user ID in the HTML (e.g. `<script>const htmlUserId = {{ current_user.id }};</script>`). The JS wrapper will decode the tab's JWT (without verifying the signature, just reading the payload) and compare its `sub` claim to `htmlUserId`. If they mismatch, the JS can visually warn the user, or we can consider the tab token completely isolated and ignore the HTML state for API requests (though this causes visual inconsistency). A safer approach is clearing the token and reloading if a mismatch is detected, effectively forcing the tab to sync with the active session cookie.
**Risks**: Brief flash of incorrect user name on full page reload before JS catches the mismatch.

## Library Findings
- **Flask-Login (0.6.3)**: 
  - *Request Loader*: The `request_loader` callback is used to authenticate a request via headers (Bearer token). It receives the Flask `request` object. 
  - *Load Order*: Flask-Login first attempts to load from the session (via `user_loader`), then falls back to `request_loader`. If a token is provided in the header, we must ensure the `request_loader` takes precedence or properly sets the `current_user` overriding the session.
  - *Session Protection*: Set via `login_manager.session_protection = "strong"`. It tracks IP and User-Agent; if they change, the session is rejected.
  - *Sources*: [Flask-Login Request Loader docs](https://flask-login.readthedocs.io/), [StackOverflow](https://stackoverflow.com/questions/36269449)
- **Flask-Session (0.8.0) & Flask (3.1.1)**:
  - *Config*: Uses `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`. Flask-Session integrates with these standard Flask config options.
  - *Sources*: [Flask Sessions](https://flask.palletsprojects.com/en/3.1.x/config/#SESSION_COOKIE_HTTPONLY)
- **PyJWT (2.9.0)**:
  - *Usage*: Validates `exp` (expiration) and `iat` (issued at) automatically if configured. Uses HS256 for symmetric signing.
  - *Exceptions*: `jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`.
  - *Sources*: [PyJWT Docs](https://pyjwt.readthedocs.io/en/stable/)
- **Cache-Control & bfcache**:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` ensures browsers do not store the page in disk/memory, preventing the Back-Forward Cache (bfcache) from showing an authenticated page after logout. `Vary: Cookie, Authorization` is also critical.
  - *Sources*: [MDN Web Docs Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
- **Browser Behavior (Tokens & Cookies)**:
  - `sessionStorage` is isolated per-tab (even same origin).
  - Cookies are scoped by host. `localhost` and `127.0.0.1` are treated as different hosts, so they maintain separate cookie jars. Cookies ignore port numbers.
  - *Sources*: [MDN Web Docs Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
- **Security / OWASP**:
  - OWASP recommends against storing JWTs in `localStorage` due to XSS risks. `sessionStorage` mitigates persistence but is still vulnerable to XSS. Cookies with `HttpOnly` and `SameSite` are preferred for primary auth. The token is an *additional* layer for tab isolation.
  - *Sources*: [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

## Risks
1. **Flask-Login Load Order**: `request_loader` normally acts as a fallback to `user_loader`. To make the token *override* the cookie, we might need a custom `before_request` hook or carefully manage the `request_loader` to prioritize the header over the session.
2. **XSS Vulnerability**: Storing JWT in `sessionStorage` makes it readable by JS, so any XSS vulnerability in the app could steal the token.
3. **Cache-Control side effects**: Disabling cache for HTML could increase server load, though it's necessary for security. We must ensure static assets bypass this.

## Recommended Order
1. Cache-Control Header Hardening (Phase 2)
2. Cookie Hardening (Phase 3)
3. Per-Tab Tokens (Phase 4)

## Open Questions
- Should the per-tab token refresh automatically, or simply expire and force the user to re-auth? (A simple strategy is extending the token upon API activity if it's near expiration).
- How strictly should we handle the user-mismatch between the tab's token and the session cookie on full page reloads?
