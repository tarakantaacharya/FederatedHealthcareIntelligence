#!/usr/bin/env python3
"""Test new prediction service with correct setup"""
import requests
import json
import sys
import sqlite3

BASE_URL = "http://localhost:8000"

# First, check what hospitals exist
def check_hospitals():
    """Check hospitals in database"""
    conn = sqlite3.connect("D:/federated-healthcare/data/federated.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, hospital_name FROM hospitals LIMIT 5")
    hospitals = cursor.fetchall()
    conn.close()
    return hospitals

def register_test_hospital():
    """Register a test hospital if needed"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "hospital_name": "City General Hospital",
            "hospital_id": "CGH-001",
            "contact_email": "admin@citygeneral.com",
            "location": "New York",
            "password": "TestPass123!"
        }
    )
    print(f"Register status: {resp.status_code}")
    return resp.status_code in [200, 409]  # 409 if already exists

def test_prediction():
    """Test prediction with new code"""
    # Register or verify hospital exists
    print("Setting up hospital...")
    register_test_hospital()
    
    # Login
    print("\nLogging in...")
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "hospital_id": "CGH-001",
            "password": "TestPass123!"
        }
    )
    
    print(f"Login status: {login_resp.status_code}")
    if login_resp.status_code != 200:
        print(f"Login response: {login_resp.text}")
        return False
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test prediction on model 3
    print("\nTesting prediction on model 3...")
    pred_resp = requests.post(
        f"{BASE_URL}/api/predictions/forecast",
        json={"model_id": 3, "forecast_horizon": 24},
        headers=headers
    )
    
    print(f"Prediction status: {pred_resp.status_code}")
    response_json = pred_resp.json()
    print(f"Response (first 500 chars): {json.dumps(response_json, indent=2)[:500]}...")
    
    if pred_resp.status_code == 200:
        print("\n✅ PREDICTION SUCCESSFUL!")
        return True
    else:
        print(f"\n❌ PREDICTION FAILED")
        if "detail" in response_json:
            print(f"Error: {response_json['detail']}")
        return False

if __name__ == "__main__":
    print("=== Checking existing hospitals ===")
    hospitals = check_hospitals()
    for hosp_id, name in hospitals:
        print(f"  {hosp_id}: {name}")
    
    print("\n=== Running prediction test ===")
    success = test_prediction()
    sys.exit(0 if success else 1)
