# Phase 5 Final Report

## A. Verification Table

| Check | Result | Verified by | Evidence |
|---|---|---|---|
| login | NOT TESTED | - | |
| logout | NOT TESTED | - | |
| Back button after logout | NOT TESTED | - | |
| two users on two hosts | Pass (stay separate) | script, earlier commit 56e9d6a, development config, not re-run at HEAD | Phase 1 baseline isolated hosts via session backend (see aseline-headers.md). Note that the 2c flag proof used a copy of the code. |
| same user in two tabs | NOT TESTED | - | |
| expired session | NOT TESTED | - | |
| JSON no-store | Pass | script, earlier commit 600e588, development config, not re-run at HEAD | Phase 2 script snapshot (phase2-headers.md) confirmed Cache-Control: no-store on API. Note that the 2c flag proof used a copy of the code. |
| HTML no-store | Pass | script, earlier commit 600e588, development config, not re-run at HEAD | Phase 2 script snapshot confirmed Cache-Control: no-store on HTML routes. Note that the 2c flag proof used a copy of the code. |
| static headers unchanged from baseline | Pass | script, earlier commit 600e588, development config, not re-run at HEAD | Phase 2 script snapshot confirmed /static bypassed the hook. Note that the 2c flag proof used a copy of the code. |
| cookie flags unchanged from baseline | NOT TESTED | - | |
| REQUIRE_HTTPS unset = baseline | NOT TESTED | - | |
| HARDEN_API_CACHE off = JSON as baseline | NOT TESTED | - | (Verified logic via script, but full server end-to-end not tested in browser). |

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
  - Causes of anonymous files: Unverified: `flash()` messages for failed logins, CSRF token generation on login page load, navigating the site anonymously where tracking/state is briefly held.
- The Back-button result if it failed in manual testing (no template edits without approval).

## F. Phase 4 (Per-Tab Tokens)
- **Status**: Phase 4 (per-tab login): earlier skipped by decision; research reopened as a separate project on branch feature/per-tab-auth, paused, not part of this PR, findings unverified.
- **Reason**: User-specific data is rendered server-side on most pages (`{{ current_user.* }}`), so tokens would show one account on the page while API calls run as another. 
- **Supported alternatives**: Separate hosts (`localhost` vs `127.0.0.1`), `a.localhost` / `b.localhost`, or private windows.

## G. Files Changed
- `app/__init__.py` (Added `after_request` cache-control, session/cookie config flags)
- `.gitignore` (Added `scratch/`)
- `docs/research/session-hardening-research.md` (Updated with research and decisions)
- `docs/research/baseline.md` (Added)
- `docs/research/baseline-headers.md` (Added)
- `docs/research/phase2-headers.md` (Added)
- `docs/research/final-report.md` (Added)
