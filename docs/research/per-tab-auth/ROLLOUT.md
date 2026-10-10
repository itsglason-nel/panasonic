# Rollout

## 1. Quiet time, flag off
In the live folder `git status` must show only the three migration lines, then `git merge feature/per-tab-auth` (stop on conflicts, `git merge --abort`). Restart the launcher, confirm login and wall screens behave as before.

## 2. Shift change
Add `ENABLE_TAB_SESSIONS=1` to the live `.env` and restart. Everyone logs in once and wall screens need their address typed again.

## 3. Rollback
Set `ENABLE_TAB_SESSIONS=0` or remove it and restart.

## What Operators Will Notice
- Address shows `/t/<code>/`.
- A new tab with the plain address asks for a login.
- Closing a tab ends that login.
- Duplicating a tab shares the login.
- A bookmark without the prefix asks for a login each time.
