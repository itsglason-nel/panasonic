import urllib.request
import json

try:
    req = urllib.request.Request('http://127.0.0.1:8080/admin/api/audit-logs')
    # We need to simulate a login or just see the HTTP status code
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Body:", response.read().decode('utf-8')[:200])
except Exception as e:
    print("Error:", e)
