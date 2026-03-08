"""
Test API to see if aggregation metrics are returned
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Login
print("=== Step 1: Authenticate ===")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"hospital_id": "CGH-001", "password": "hospital123"}
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"  Response: {login_response.text}")
    exit(1)

login_data = login_response.json()
token = login_data["access_token"]
print(f"✓ Authenticated successfully")
print(f"  Token: {token[:30]}...")

# Step 2: Get aggregation rounds
print("\n=== Step 2: Query Aggregation Rounds ===")
headers = {"Authorization": f"Bearer {token}"}
rounds_response = requests.get(f"{BASE_URL}/api/aggregation/rounds", headers=headers)

if rounds_response.status_code != 200:
    print(f"✗ Get rounds failed: {rounds_response.status_code}")
    print(f"  Response: {rounds_response.text}")
    exit(1)

rounds_data = rounds_response.json()
print(f"✓ Retrieved {len(rounds_data)} rounds")

# Step 3: Display round metrics
print("\n=== Round Metrics ===")
for round_info in rounds_data:
    print(f"\nRound {round_info['round_number']}:")
    print(f"  Participating Hospitals: {round_info.get('num_participating_hospitals', 'N/A')}")
    print(f"  Status: {round_info.get('status', 'N/A')}")
    print(f"  Metrics:")
    print(f"    - Average Loss: {round_info.get('average_loss', 'NULL')}")
    print(f"    - Average MAPE: {round_info.get('average_mape', 'NULL')}")
    print(f"    - Average RMSE: {round_info.get('average_rmse', 'NULL')}")
    print(f"    - Average R2: {round_info.get('average_r2', 'NULL')}")
    print(f"    - Average Accuracy: {round_info.get('average_accuracy', 'NULL')}")

# Step 4: Get detailed round information
if rounds_data:
    print(f"\n=== Step 4: Get Round Detail (Round 2) ===")
    detail_response = requests.get(f"{BASE_URL}/api/aggregation/round/2", headers=headers)
    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        print(f"Round Detail Response:")
        print(json.dumps(detail_data, indent=2))
    else:
        print(f"Could not get round detail: {detail_response.status_code}")
