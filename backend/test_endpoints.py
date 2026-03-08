import requests

endpoints = [
    ("POST", "http://localhost:8000/api/admin/login", {"admin_id": "CENTRAL-001", "password": "admin123"}),
    ("GET", "http://localhost:8000/api/aggregation/rounds", None),
    ("GET", "http://localhost:8000/api/aggregation/global-model", None),
    ("GET", "http://localhost:8000/api/blockchain/logs", None),
]

print("=== ENDPOINT STATUS CODES ===\n")
for method, url, data in endpoints:
    try:
        if method == "POST":
            resp = requests.post(url, json=data, timeout=5)
        else:
            resp = requests.get(url, timeout=5)
        print(f"{method:4} {url.split('/api/')[-1]:40} → {resp.status_code}")
    except Exception as e:
        print(f"{method:4} {url.split('/api/')[-1]:40} → ERROR: {type(e).__name__}")
