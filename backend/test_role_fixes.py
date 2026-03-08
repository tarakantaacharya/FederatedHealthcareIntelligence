#!/usr/bin/env python3
"""Quick test of role-based access fixes"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("=== TEST 1: Register Regular Hospital (role=HOSPITAL by default) ===")
reg_data = {
    'hospital_name': 'Regular Hospital Test',
    'hospital_id': 'REG-TEST-001',
    'contact_email': 'regular@test.hospital',
    'location': 'Test City',
    'password': 'TestPass123!'
}
resp = requests.post(f'{BASE_URL}/api/auth/register', json=reg_data)
print(f"Status: {resp.status_code}")

print("\n=== TEST 2: Register Admin Hospital (role=ADMIN) ===")
admin_reg_data = {
    'hospital_name': 'Admin Hospital Test',
    'hospital_id': 'ADM-TEST-001',
    'contact_email': 'admin@test.hospital',
    'location': 'Test City',
    'password': 'AdminPass123!',
    'role': 'ADMIN'
}
resp = requests.post(f'{BASE_URL}/api/auth/register', json=admin_reg_data)
print(f"Status: {resp.status_code}")

print("\n=== TEST 3: Login as Admin ===")
admin_login = {'hospital_id': 'ADM-TEST-001', 'password': 'AdminPass123!'}
resp = requests.post(f'{BASE_URL}/api/auth/login', json=admin_login)
print(f"Status: {resp.status_code}")
admin_token = resp.json().get('access_token')
print(f"Token obtained: {admin_token[:50]}...")

print("\n=== TEST 4: Login as Regular Hospital ===")
reg_login = {'hospital_id': 'REG-TEST-001', 'password': 'TestPass123!'}
resp = requests.post(f'{BASE_URL}/api/auth/login', json=reg_login)
print(f"Status: {resp.status_code}")
reg_token = resp.json().get('access_token')
print(f"Token obtained: {reg_token[:50]}...")

print("\n=== TEST 5: Try Aggregation with Regular Token (should FAIL 403) ===")
headers = {'Authorization': f'Bearer {reg_token}'}
payload = {'round_number': 1}
resp = requests.post(f'{BASE_URL}/api/aggregation/fedavg', json=payload, headers=headers)
print(f"Status: {resp.status_code} (expected 403 Forbidden)")
print(f"Detail: {resp.json().get('detail', 'N/A')}")

print("\n=== TEST 6: Try Aggregation with Admin Token (should SUCCEED past role check) ===")
headers = {'Authorization': f'Bearer {admin_token}'}
payload = {'round_number': 1}
resp = requests.post(f'{BASE_URL}/api/aggregation/fedavg', json=payload, headers=headers)
print(f"Status: {resp.status_code} (expected 200 or error from aggregation logic, not 401/403)")
if resp.status_code != 200:
    print(f"Detail: {resp.json().get('detail', 'N/A')}")

print("\n✓ ROLE-BASED ACCESS CONTROL VERIFICATION COMPLETE")
