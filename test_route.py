from app import create_app
import json

app = create_app()
with app.app_context():
    client = app.test_client()
    # Need to simulate login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'super_admin'
    
    resp = client.get('/admin/api/schedules?date=10/05/2026&line_id=L1')
    data = json.loads(resp.data)
    print(json.dumps(data.get('wip_status'), indent=2))
