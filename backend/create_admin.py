import sqlite3
from passlib.context import CryptContext

# Initialize password context (matches security.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash the password
hashed_password = pwd_context.hash("admin123")
print(f"Hashed password: {hashed_password}\n")

# Connect and insert
conn = sqlite3.connect('federated.db')
cursor = conn.cursor()

try:
    # Insert admin record
    cursor.execute("""
    INSERT INTO admins (admin_id, admin_name, contact_email, hashed_password, role, is_active, is_super_admin)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("CENTRAL-001", "Central Server Admin", "admin@central.com", hashed_password, "ADMIN", True, True))
    
    conn.commit()
    print("✓ Admin record created")
    
    # Verify
    cursor.execute("SELECT admin_id, admin_name, contact_email FROM admins WHERE admin_id = 'CENTRAL-001'")
    row = cursor.fetchone()
    if row:
        print(f"✓ Verified: {row}\n")
    
except Exception as e:
    print(f"✗ Error: {e}\n")
    conn.rollback()
finally:
    conn.close()
