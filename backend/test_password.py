from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash from database for CENTRAL-001
hash_from_db = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

# Test passwords
passwords = ["password", "admin123", "Password123", "admin", "Password"]

print("Testing password hash verification:")
print(f"Hash: {hash_from_db}\n")

for pwd in passwords:
    try:
        result = pwd_context.verify(pwd, hash_from_db)
        print(f"'{pwd}': {result}")
        if result:
            print(f"  ✓ MATCH FOUND: '{pwd}'")
    except Exception as e:
        print(f"'{pwd}': ERROR - {e}")

# Also generate new hash for "password"
print("\n\nGenerating new hash for 'password':")
new_hash = pwd_context.hash("password")
print(f"New hash: {new_hash}")
print(f"Verify: {pwd_context.verify('password', new_hash)}")
