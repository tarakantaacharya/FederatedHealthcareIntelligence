"""Test training through REAL API route (not direct function call)"""
import requests
import json
import sys

# Fix encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_api_training():
    """Test POST /api/training/start via HTTP"""
    
    print("\n" + "="*70)
    print("TESTING TRAINING VIA REAL API ROUTE")
    print("="*70)
    
    # Step 1: Login as CGH-001
    print("\n[Step 1] Login to hospital CGH-001...")
    login_data = {
        "hospital_id": "CGH-001",
        "password": "TestHospital123!"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if resp.status_code != 200:
            print(f"[FAIL] Login failed: {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
        
        auth_result = resp.json()
        token = auth_result.get('access_token')
        print(f"[OK] Login successful")
        
    except Exception as e:
        print(f"[FAIL] Login exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Call training endpoint via HTTP
    print("\n[Step 2] POST /api/training/start via HTTP...")
    print(f"  Dataset ID: 1")
    print(f"  Target: flu_cases (from active round)")
    print(f"  Epochs: 1")
    
    training_request = {
        "dataset_id": 1,
        "epochs": 1
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"\n  Sending POST request to {BASE_URL}/api/training/start...")
        resp = requests.post(
            f"{BASE_URL}/api/training/start",
            json=training_request,
            headers=headers,
            timeout=120
        )
        
        print(f"\n[Response] HTTP Status: {resp.status_code}")
        
        if resp.status_code in [200, 201]:
            print("[SUCCESS] HTTP 200/201 received!")
            result = resp.json()
            
            print("\n" + "="*70)
            print("TRAINING SUCCESSFUL - RESULTS:")
            print("="*70)
            print(f"  Model ID: {result.get('model_id')}")
            print(f"  Model Path: {result.get('model_path')}")
            print(f"  Model Type: {result.get('model_used')}")
            print(f"  Status: {result.get('status')}")
            
            if 'metrics' in result:
                metrics = result['metrics']
                print(f"\n  Metrics:")
                print(f"    - Train Loss: {metrics.get('train_loss')}")
                print(f"    - Epsilon Spent: {metrics.get('epsilon_spent')}")
                print(f"    - Delta: {metrics.get('delta')}")
                print(f"    - Epochs: {metrics.get('num_epochs')}")
                print(f"    - Device: {metrics.get('device')}")
                print(f"    - DP Method: {metrics.get('dp_method')}")
            
            print("\n" + "="*70)
            print("✓ NO tuple.detach error")
            print("✓ NO hidden exception")
            print("✓ Training completed successfully via API")
            print("="*70)
            return True
            
        else:
            print(f"[FAIL] HTTP {resp.status_code}")
            print(f"\nResponse Body:")
            try:
                error_detail = resp.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print(resp.text)
            
            print("\n" + "="*70)
            print("ERROR OCCURRED - CHECK BACKEND LOGS")
            print("="*70)
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timeout (120s)")
        return False
    except Exception as e:
        print(f"[FAIL] Exception during API call: {type(e).__name__}: {e}")
        import traceback
        print("\nFull Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_training()
    sys.exit(0 if success else 1)
