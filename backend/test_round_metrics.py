#!/usr/bin/env python3
"""Test if round 2 details include hospital metrics"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"hospital_id": "CGH-001", "password": "password123"}
)

token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("Getting Round 2 details...")
print("=" * 80)

# Get round 2 details
response = requests.get(
    f"{BASE_URL}/api/rounds/2",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    contributions = data.get("hospital_contributions", [])
    
    print(f"Status: {response.status_code}")
    print(f"Participating Hospitals: {len(contributions)}")
    print()
    
    for hospital in contributions:
        print(f"Hospital: {hospital.get('hospital_name')} (ID: {hospital.get('hospital_id')})")
        print(f"  Loss: {hospital.get('loss')}")
        print(f"  Accuracy: {hospital.get('accuracy')}")
        print(f"  MAPE: {hospital.get('mape')}")
        print(f"  RMSE: {hospital.get('rmse')}")
        print(f"  R²: {hospital.get('r2')}")
        print(f"  Uploaded: {hospital.get('uploaded_at')}")
        print()
else:
    print(f"Failed: {response.status_code}")
    print(response.text)

# Also check central aggregation fields
print("\nRound 2 Aggregated Metrics:")
print("-" * 80)
print(f"Average Loss: {data.get('average_loss')}")
print(f"Average Accuracy: {data.get('average_accuracy')}")
print(f"Average MAPE: {data.get('average_mape')}")
print(f"Average RMSE: {data.get('average_rmse')}")
print(f"Average R²: {data.get('average_r2')}")
