import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from app.utils.security import hash_password, verify_password

# Create fresh hash
test_password = "hospital123"
fresh_hash = hash_password(test_password)

print(f"Fresh hash for '{test_password}':")
print(f"  {fresh_hash}")

# Test the fresh hash
print(f"\nVerifying fresh hash...")
verify_result = verify_password(test_password, fresh_hash)
print(f"  Verification result: {verify_result}")

# Update database
engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')
with engine.begin() as conn:
    conn.execute(
        text("UPDATE hospitals SET hashed_password = :pwd_hash WHERE hospital_id = 'CGH-001'"),
        {"pwd_hash": fresh_hash}
    )
    print(f"\n✓ Updated CGH-001 with fresh hash")

# Verify in database
with engine.connect() as conn:
    result = conn.execute(text("SELECT hashed_password FROM hospitals WHERE hospital_id = 'CGH-001'"))
    db_hash = result.fetchone()[0]
    print(f"\n✓ Verified in database:")
    print(f"  Hash: {db_hash[:40]}...")
    
    # Test verification with DB hash
    db_verify = verify_password(test_password, db_hash)
    print(f"  Verification: {db_verify}")
