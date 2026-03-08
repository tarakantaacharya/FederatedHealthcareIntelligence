import sys
sys.path.insert(0, '.')
from app.utils.security import verify_password

# The password hash that was set
password_hash = "$2b$12$pEV4P58ASeO9pfDcGyv/su32OCScSMK3KtPsfR6bojD5laPcLGZPK"

# The password we're trying
test_password = "hospital123"

# Test verification
try:
    result = verify_password(test_password, password_hash)
    print(f"✓ Password verification result: {result}")
    if not result:
        print("  Password verification FAILED - hash doesn't match")
    else:
        print("  Password verification PASSED")
except Exception as e:
    print(f"✗ Error during verification: {e}")
