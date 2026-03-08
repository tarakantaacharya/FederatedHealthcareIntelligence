import requests

print("\n" + "=" * 60)
print("BLOCKCHAIN ENDPOINT TEST")
print("=" * 60)

# Get admin token
try:
    resp = requests.post(
        "http://localhost:8000/api/admin/login",
        json={"admin_id": "CENTRAL-001", "password": "admin123"},
        timeout=5
    )
    
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print(f"✓ Admin token received")
        
        # Test blockchain logs endpoint
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(
            "http://localhost:8000/api/blockchain/logs",
            headers=headers,
            timeout=5
        )
        
        print(f"GET /api/blockchain/logs → {resp.status_code}")
        print(f"Response: {resp.json()}\n")
    else:
        print(f"✗ Login failed: {resp.status_code}")
        
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
