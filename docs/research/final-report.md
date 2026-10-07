# Phase 5 Final Report

## A. Verification Table

| Check | Result | Verified by | Evidence |
|---|---|---|---|
| login | NOT TESTED | my browser | |
| logout | NOT TESTED | my browser | |
| Back button after logout | NOT TESTED | my browser | |
| two users on two hosts | Pass (stay separate) | script | Phase 1 baseline isolated hosts via session backend (see `baseline-headers.md`). |
| same user in two tabs | NOT TESTED | my browser | |
| expired session | NOT TESTED | my browser | |
| JSON no-store | Pass | script | Phase 2 script snapshot (`phase2-headers.md`) confirmed `Cache-Control: no-store` on API. |
| HTML no-store | Pass | script | Phase 2 script snapshot confirmed `Cache-Control: no-store` on HTML routes. |
| static headers unchanged from baseline | Pass | script | Phase 2 script snapshot confirmed `/static` bypassed the hook. |
| cookie flags unchanged from baseline | Pass | script | Phase 3 script test (`test_phase3_helper.py`) confirmed flags unchanged with `REQUIRE_HTTPS` unset. |
| REQUIRE_HTTPS unset = baseline | Pass | script | Phase 3 script test output matched Phase 1 baseline. |
| HARDEN_API_CACHE off = JSON as baseline | NOT TESTED | my browser | (Verified logic via script, but full server end-to-end not tested in browser). |

## B. Flags
- `HARDEN_API_CACHE`: Default is ON. Accepted values: `1`, `true`, `yes`, `on` for True; `0`, `false`, `no`, `off` for False.
  - What can log users out: Nothing. It only affects the `Cache-Control` header on API and HTML responses to prevent bfcache ghosts.
- `REQUIRE_HTTPS`: Default is OFF. Accepted values: `1`, `true`, `yes`, `on` for True; `0`, `false`, `no`, `off` for False.
  - What can log users out: Setting it to ON in a plain HTTP environment. Browsers will refuse the `Secure` cookie and instantly log everyone out.
- **Expected Baseline**: Cookie `pmpc_session` must show HttpOnly checked, Path=/, SameSite=Lax, Secure unchecked.

## C. Rollback
- **Fastest Rollback**: Unset `REQUIRE_HTTPS` and `HARDEN_API_CACHE` in the environment and restart the launcher.
- **Git Revert**: Use `git revert <hash>` followed by a normal push:
  - Phase 2 (Cache-Control): `git revert aca0fc0`
  - Phase 3 (Cookie Hardening): `git revert c95a893`
- **Tags applied**: 
  - `checkpoint-baseline`
  - `checkpoint-phase-2`
  - `checkpoint-phase-2b`
  - `checkpoint-phase-2c`
  - `checkpoint-phase-3`

## D. Cleanup Checklist
- [x] Test users 4 and 5 gone: Re-run query confirmed 0 rows for ids 4, 5, or `test_user_%`.
- [x] Session files gone: The 2 specific files for users 4 and 5 were deleted during Phase 2 cleanup.
- [x] Phase 5 items from earlier docs: Verified.

## E. Open Items (For User, Not Fixed Here)
- Silent Redis-to-filesystem fallback on startup (horizontal scaling risk).
- 31-day idle lifetime for active sessions (refreshing on every request).
- Tracked `scratch/fix_admin.py` which executes live DB writes to `WorkSched` and `linestat`.
- Committed Keyence manual PDF in the codebase history.
- Empty `.db` initialization files (SQLite) committed in git history.
- Session folder threshold: the threshold counts session FILES (anonymous and not-yet-expired included); pruning removes the least recently active first; counts on Oct 7 2026 are 174 total, 68 anonymous; watch the file count, no change made.
  - Causes of anonymous files: Verified: `flash()` messages for failed logins, CSRF token generation on login page load. Unverified (guess): navigating the site anonymously where tracking/state is briefly held.
- The Back-button result if it failed in manual testing (no template edits without approval).

## F. Phase 4 (Per-Tab Tokens)
- **Status**: Skipped by decision. per-tab login: research started on branch feature/per-tab-auth, paused, NOT part of this PR, its findings are unverified.
- **Reason**: User-specific data is rendered server-side on most pages (`{{ current_user.* }}`), so tokens would show one account on the page while API calls run as another. 
- **Supported alternatives**: Separate hosts (`localhost` vs `127.0.0.1`), `a.localhost` / `b.localhost`, or private windows. Not a failure and not a TODO.

## G. Files Changed
- `app/__init__.py` (Added `after_request` cache-control, session/cookie config flags)
- `.gitignore` (Added `.flask_sessions/`)
- `docs/research/session-hardening-research.md` (Updated with research and decisions)
- `docs/research/baseline.md` (Added)
- `docs/research/baseline-headers.md` (Added)
- `docs/research/phase2-headers.md` (Added)
- `docs/research/final-report.md` (Added)
