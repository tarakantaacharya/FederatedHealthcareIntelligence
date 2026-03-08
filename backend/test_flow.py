import requests

print("=" * 60)
print("ADMIN LOGIN TEST")
print("=" * 60)

# Test admin login
try:
    resp = requests.post(
        "http://localhost:8000/api/admin/login",
        json={"admin_id": "CENTRAL-001", "password": "admin123"},
        timeout=5
    )
    print(f"POST /api/admin/login → {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token")
        print(f"✓ Token received: {token[:20]}...")
        
        # Test protected endpoints with token
        print("\n" + "=" * 60)
        print("PROTECTED ENDPOINTS WITH TOKEN")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {token}"}
        
        protected = [
            ("GET", "http://localhost:8000/api/aggregation/rounds"),
            ("GET", "http://localhost:8000/api/aggregation/global-model"),
            ("GET", "http://localhost:8000/api/blockchain/logs"),
        ]
        
        for method, url in protected:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                print(f"{method} {url.split('/api/')[-1]:35} → {resp.status_code}")
            except Exception as e:
                print(f"{method} {url.split('/api/')[-1]:35} → ERROR: {type(e).__name__}")
    else:
        print(f"✗ Login failed: {resp.text}")
        
except Exception as e:
    print(f"✗ Login error: {type(e).__name__}: {e}")
