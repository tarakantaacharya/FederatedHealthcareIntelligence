#!/usr/bin/env python3
"""Quick test of new prediction service with target_column query"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_prediction():
    """Test prediction endpoint with new code"""
    # First login
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "hospital_id": "CGH-001",
            "password": "Test123!@"
        }
    )
    
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code}")
        print(login_resp.text)
        return False
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Now test prediction on model 3
    pred_resp = requests.post(
        f"{BASE_URL}/api/predictions/forecast",
        json={"model_id": 3, "forecast_horizon": 24},
        headers=headers
    )
    
    print(f"Status: {pred_resp.status_code}")
    print(f"Response: {json.dumps(pred_resp.json(), indent=2)}")
    
    return pred_resp.status_code == 200

if __name__ == "__main__":
    success = test_prediction()
    sys.exit(0 if success else 1)
