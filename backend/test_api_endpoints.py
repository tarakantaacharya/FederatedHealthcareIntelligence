"""Test API endpoints after .env fix"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1️⃣ Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
        return True
    return False

def test_register():
    """Test hospital registration"""
    print("\n2️⃣ Testing Hospital Registration...")
    payload = {
        "hospital_name": "Alembic Test Hospital",
        "hospital_id": "ALEMBIC-TEST-001",
        "contact_email": "test@alembic-hospital.com",
        "location": "Test City",
        "password": "SecurePass123!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"   Success: Hospital registered")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_login():
    """Test hospital login"""
    print("\n3️⃣ Testing Hospital Login...")
    payload = {
        "hospital_id": "ALEMBIC-TEST-001",
        "password": "SecurePass123!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: Token received")
        print(f"   Hospital ID: {data.get('hospital_id')}")
        return True, data.get('access_token')
    else:
        print(f"   Error: {response.text}")
        return False, None

def test_admin_login():
    """Test admin login"""
    print("\n4️⃣ Testing Admin Login...")
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/admin/auth/login", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Success: Admin logged in")
        return True
    else:
        print(f"   Info: Admin may need to be created first")
        return False

if __name__ == "__main__":
    print("="*60)
    print("API ENDPOINT VALIDATION - POST .ENV FIX")
    print("="*60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health", test_health()))
    
    # Test 2: Register
    results.append(("Register", test_register()))
    
    # Test 3: Login
    login_success, token = test_login()
    results.append(("Login", login_success))
    
    # Test 4: Admin Login (optional)
    results.append(("Admin Login", test_admin_login()))
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_critical_passed = all(passed for name, passed in results[:3])
    if all_critical_passed:
        print("\n✅ ALL CRITICAL TESTS PASSED")
        print("🎉 .ENV FIX SUCCESSFUL - ORM ALIGNED WITH DATABASE")
    else:
        print("\n⚠️ SOME TESTS FAILED")
