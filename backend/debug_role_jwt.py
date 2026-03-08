#!/usr/bin/env python3
"""Debug role assignment in JWT token"""
import requests
import json
import base64
import sys

BASE_URL = 'http://localhost:8000'

admin_id = 'DEBUG-ADMIN-UNQ'
admin_name = 'Debug Admin Hospital'

print("=== STEP 1: Register Admin Hospital with role=ADMIN ===")
admin_reg_data = {
    'hospital_name': admin_name,
    'hospital_id': admin_id,
    'contact_email': f'{admin_id}@test.hospital',
    'location': 'Test City',
    'password': 'DebugAdminPass123!',
    'role': 'ADMIN'
}
resp = requests.post(f'{BASE_URL}/api/auth/register', json=admin_reg_data)
print(f"Register Status: {resp.status_code}")
print(f"Response: {resp.json()}")

if resp.status_code != 201 and resp.status_code != 200:
    print("Registration failed!")
    sys.exit(1)

print("\n=== STEP 2: Login and Inspect JWT ===")
resp = requests.post(f'{BASE_URL}/api/auth/login', json={'hospital_id': admin_id, 'password': 'DebugAdminPass123!'})
print(f"Login Status: {resp.status_code}")
token = resp.json().get('access_token')

# Decode JWT to see payload
try:
    parts = token.split('.')
    payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64)
    payload = json.loads(payload_json)
    print(f"\nJWT Payload:")
    for key, value in payload.items():
        print(f"  {key}: {value}")
    print(f"\nRole in JWT: {payload.get('role', 'NOT FOUND')}")
except Exception as e:
    print(f"Error decoding JWT: {e}")

print("\n=== STEP 3: Try Aggregation Endpoint ===")
headers = {'Authorization': f'Bearer {token}'}
resp = requests.post(f'{BASE_URL}/api/aggregation/fedavg', json={'round_number': 1}, headers=headers)
print(f"Aggregation Status: {resp.status_code}")
print(f"Aggregation Response: {json.dumps(resp.json(), indent=2)}")

if resp.status_code == 403:
    print("\n✗ ISSUE: Admin token still being rejected as HOSPITAL role")
elif resp.status_code == 200:
    print("\n✓ SUCCESS: Admin token accepted past role check")
else:
    print(f"\n? Unexpected status: {resp.status_code}")
