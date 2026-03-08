#!/usr/bin/env python3
"""
Verify metrics are in hospital contributions
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# First get a token by logging in as an admin
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"hospital_id": "ADMIN-001", "password": "admin"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json().get('access_token')
headers = {"Authorization": f"Bearer {token}"}

print("=" * 80)
print("HOSPITAL CONTRIBUTIONS METRICS VERIFICATION")
print("=" * 80)

# Get round 2 details
response = requests.get(
    f"{BASE_URL}/api/rounds/2",
    headers=headers
)

print(f"\nAPI Response Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    contributions = data.get('hospital_contributions', [])
    
    print(f"\nParticipating Hospitals: {len(contributions)}")
    print("\nMetrics per hospital:")
    print("-" * 80)
    
    for hospital in contributions:
        print(f"\n{hospital.get('hospital_name')} (ID: {hospital.get('hospital_id')})")
        print(f"  Loss: {hospital.get('loss')}")
        print(f"  Accuracy: {hospital.get('accuracy')}")
        print(f"  MAPE: {hospital.get('mape')} ← Should NOT be N/A")
        print(f"  RMSE: {hospital.get('rmse')} ← Should NOT be N/A")
        print(f"  R²: {hospital.get('r2')} ← Should NOT be N/A")
        print(f"  Uploaded: {hospital.get('uploaded_at')}")
        
        # Check for N/A values
        has_metrics = (
            hospital.get('mape') is not None and 
            hospital.get('rmse') is not None and 
            hospital.get('r2') is not None
        )
        
        if has_metrics:
            print(f"  ✓ Metrics present!")
        else:
            print(f"  ✗ PROBLEM: Metrics are NULL/N/A")
    
    # For debugging, also show the raw response
    print("\n" + "=" * 80)
    print("RAW JSON RESPONSE:")
    print("=" * 80)
    print(json.dumps(data, indent=2, default=str)[:1000] + "...")
else:
    print(f"Failed to get round details: {response.status_code}")
    print(response.text)
