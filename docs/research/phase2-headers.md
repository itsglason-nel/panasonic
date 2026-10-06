# Phase 2 Headers (Cache-Control Hardening)

| Route | Content-Type | Before `Cache-Control` | After `Cache-Control` | Notes |
|:---|:---|:---|:---|:---|
| `/auth/login` | HTML | `no-store, no-cache, must-revalidate, max-age=0` | `no-store, no-cache, must-revalidate, max-age=0` | Remained hardened |
| `/dashboard` | HTML | `no-store, no-cache, must-revalidate, max-age=0` | `no-store, no-cache, must-revalidate, max-age=0` | Remained hardened |
| `/api/lines/active` | JSON | *(None)* | `no-store, no-cache, must-revalidate, max-age=0` | **Hardened successfully** |
| `/static/css/app.css` | CSS | `no-cache` | `no-cache` | Untouched, safely bypassed |

*(Both HTML and JSON now properly output `Pragma: no-cache`, `Expires: 0`, and append `Cookie` to `Vary`)*.
