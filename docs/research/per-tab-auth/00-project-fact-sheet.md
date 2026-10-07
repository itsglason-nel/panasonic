# 00-project-fact-sheet.md

## 3a. Dashboard Check
```
--- Dashboard.html Content ---
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panasonic</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #f4f5f7;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            color: #1a1a1a;
        }
        .container {
            text-align: center;
            background: white;
            padding: 60px;
            border-radius: 24px;
            box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .module-name {
            font-size: 20px;
            color: #6b7280;
            margin-bottom: 40px;
        }
        .btn-logout {
            display: inline-block;
            padding: 12px 24px;
            background-color: #e53e3e;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-logout:hover {
            background-color: #c53030;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome, {{ current_user.full_name or current_user.username }}!</h1>
        <div class="module-name">You are logged into: <strong>{{ module }}</strong></div>
        <a href="{{ url_for('auth.logout') }}" class="btn-logout">Sign Out</a>
    </div>
</body>
</html>

--- Inherited Templates ---
```
ANALYST NOTES (INFERRED):
- `dashboard.html` extends `base.html`.
- `base.html` has no timers.
- Therefore, `/dashboard` is NOT a wall screen. It is a static page.

## 3b. Admin Textual Expansion
```
    </div>
</div>

<!-- Modal: Repair Details -->
<div id="modal-repair-details" class="modal-overlay">
    <div class="modal-content">
        <div class="modal-header">
            <h3 class="modal-title">Repair Details</h3>
            <button class="modal-close" onclick="closeModal('modal-repair-details')">&times;</button>
        </div>
        <div class="modal-body" style="text-align:center; padding: 40px 20px;">
            <p style="color:var(--text-secondary); margin-bottom:10px;">Detailed repair logs view not fully implemented
                yet.</p>
            <p><strong>Serial:</strong> <span id="repair-det-serial"></span></p>
        </div>
    </div>
```
Schedules Fetches:
```
app\templates\base.html:144 -> fetch('/api/lines/active')
app\templates\admin\components\scripts.html:338 -> fetch('/api/lines/active')
app\templates\admin\components\scripts.html:380 -> fetch(`/admin/api/schedules?date=${encodeURIComponent(date)}&line_id=${lineId}`)
app\templates\admin\components\scripts.html:428 -> fetch(`/admin/api/schedules?date=${encodeURIComponent(dateStr)}&line_id=${sched.line_code}`)
app\templates\admin\components\scripts.html:605 -> fetch(`/admin/api/schedules?date=${encodeURIComponent(dateStr)}&line_id=${targetLine}`)
app\templates\admin\components\scripts.html:931 -> fetch(`/admin/api/schedules?date=${encodeURIComponent(date)}&line_id=${lineId}`).then(r => r.json()),
app\templates\admin\components\scripts.html:1324 -> return fetch('/api/areas/active')
app\templates\admin\components\scripts.html:2147 -> fetch('/api/modules/active')
app\templates\admin\components\scripts.html:2176 -> fetch('/api/tags/active')
```
ANALYST NOTES (INFERRED):
- The `schedules?date=` is called by `fetchSchedules(date)` in `scripts.html`. It repeats because it's bound to `workSchedRefreshTimer = setInterval(..., 30000)` and might be called via UI events (like `DOMContentLoaded` or line selection) leading to 5 calls initially before settling to the 30s timer.

## 3e. Observers
```

```

## 3f. trigger-pdf
```
1510: @admin_bp.route('/admin/api/trigger-pdf/<serial>', methods=['POST'])
1511: @login_required
1512: def trigger_pdf(serial):
1513:     """Trigger the automated generation of the Production Information Tag PDF for a unit.
1514:     This can be called when a unit finishes PIT or from the UI."""
1515:     from app.services.pdf_generator import generate_tag_pdf
1516:     from flask import request
1517:     # Extract port from the request host to ensure we hit the right local server instance
1518:     try:
1519:         port = int(request.host.split(':')[1]) if ':' in request.host else 80
1520:     except ValueError:
1521:         port = 8080
1522:     
1523:     success = generate_tag_pdf(serial, port=port)
1524:     if success:
1525:         return jsonify({'success': True, 'message': f'PDF generated successfully for {serial}.'})
1526:     else:
1527:         return jsonify({'success': False, 'error': 'Failed to generate PDF. Check logs.'}), 500
1528: 
1529: def _get_tag_data(serial):
1530:     """Gather data from CRS, GMS, ATT, WCI for a specific serial number."""
```
