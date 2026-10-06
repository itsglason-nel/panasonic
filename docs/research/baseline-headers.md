# Baseline Headers Snapshot

## Login Page (GET)
- **Status**: 200
- **Cache-Control**: no-store, no-cache, must-revalidate, max-age=0
- **Pragma**: no-cache
- **Expires**: 0
- **Vary**: Cookie
- **Set-Cookie**: pmpc_session=[HIDDEN]; HttpOnly; Path=/; SameSite=Lax

## Dashboard
- **Status**: 200
- **Cache-Control**: no-store, no-cache, must-revalidate, max-age=0
- **Pragma**: no-cache
- **Expires**: 0
- **Vary**: Cookie

## API /api/lines/active
- **Status**: 200
- **Vary**: Cookie
*(Note: No Cache-Control is currently set for the API).*

## Static File (`/static/css/app.css`)
- **Status**: 200
- **Cache-Control**: no-cache

## User Isolation
- User A Dashboard contains test_user_a: True
- User B Dashboard contains test_user_b: True
- User B logged in after User A logs out: True
