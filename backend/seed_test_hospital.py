"""
Reset hospital password in database for testing
"""
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from app.utils.security import hash_password

engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')

# Hash password using backend's security module
test_password = "hospital123"
password_hash = hash_password(test_password)

# Update CGH-001 password
with engine.begin() as conn:
    conn.execute(
        text("UPDATE hospitals SET hashed_password = :pwd_hash WHERE hospital_id = 'CGH-001'"),
        {"pwd_hash": password_hash}
    )
    print(f"✓ Updated CGH-001 password to: '{test_password}'")
    print(f"  Hash: {password_hash[:40]}...")

# Verify
with engine.connect() as conn:
    result = conn.execute(text("SELECT hospital_id, hospital_name FROM hospitals WHERE hospital_id = 'CGH-001'"))
    row = result.fetchone()
    if row:
        print(f"\n✓ Verified hospital: {row[0]} - {row[1]}")
