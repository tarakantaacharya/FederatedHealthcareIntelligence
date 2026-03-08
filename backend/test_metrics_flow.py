#!/usr/bin/env python3
"""
Test script to trigger training and observe metrics flow
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("METRICS FLOW TEST")
print("=" * 80)

# Step 1: Check active rounds
print("\n[1] Checking active rounds...")
response = requests.get(
    f"{BASE_URL}/api/aggregation/rounds",
    headers={"Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}  # Needs valid token
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    rounds = response.json()
    if rounds:
        print(f"Found {len(rounds)} rounds")
        for r in rounds:
            print(f"  - Round {r.get('round_number')}: Status={r.get('status')}")
else:
    print("Could not retrieve rounds (likely auth issue)")

# Step 2: Check if there's training happening
print("\n[2] Checking hospital metrics...")
response = requests.get(
    f"{BASE_URL}/api/health"
)
print(f"Backend health: {response.status_code}")

print("\n[3] Checking database directly for current metrics state...")
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///data/federated.db')
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT COUNT(*) cnt, 
               COUNT(CASE WHEN local_mape IS NOT NULL THEN 1 END) with_mape,
               COUNT(CASE WHEN local_rmse IS NOT NULL THEN 1 END) with_rmse,
               COUNT(CASE WHEN local_r2 IS NOT NULL THEN 1 END) with_r2
        FROM model_weights 
        WHERE is_global = 0 AND hospital_id IS NOT NULL
    """))
    row = result.fetchone()
    print(f"Hospital models: {row[0]} total")
    print(f"  - With MAPE: {row[1]}")
    print(f"  - With RMSE: {row[2]}")
    print(f"  - With R2:   {row[3]}")
    
    # Check backend.log for metrics logs
    print("\n[4] Checking recent backend logs for metrics...")
    try:
        with open('backend.log', 'r') as f:
            lines = f.readlines()
            metrics_lines = [l for l in lines if '[METRICS' in l or '✓ TFT validation' in l or '✓ Fallback' in l or '⚠ Using training' in l]
            if metrics_lines:
                print("Recent metrics logs:")
                for line in metrics_lines[-10:]:
                    print(f"  {line.strip()}")
            else:
                print("No metrics logs found yet")
    except FileNotFoundError:
        print("backend.log not found")

print("\n" + "=" * 80)
print("TEST COMPLETE - Check logs for metrics computation status")
print("=" * 80)
