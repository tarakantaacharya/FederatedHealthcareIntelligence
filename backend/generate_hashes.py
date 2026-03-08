from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

admin_pwd = "admin123"
hospital_pwd = "hospital123"

admin_hash = pwd_context.hash(admin_pwd)
hospital_hash = pwd_context.hash(hospital_pwd)

print(f"Admin password: {admin_pwd}")
print(f"Admin hash: {admin_hash}")
print(f"Verify: {pwd_context.verify(admin_pwd, admin_hash)}\n")

print(f"Hospital password: {hospital_pwd}")
print(f"Hospital hash: {hospital_hash}")
print(f"Verify: {pwd_context.verify(hospital_pwd, hospital_hash)}\n")

# Generate SQL
print("\n--- SQL to insert ---")
print(f"-- Admin (admin123)")
print(f"INSERT INTO admins (admin_id, admin_name, contact_email, hashed_password, role, is_active, is_super_admin)")
print(f"VALUES ('CENTRAL-001', 'Central Admin', 'admin@central.com', '{admin_hash}', 'ADMIN', TRUE, TRUE);")

print(f"\n-- Hospital (hospital123)")
print(f"INSERT INTO hospitals (hospital_name, hospital_id, contact_email, location, hashed_password, is_active, is_verified, role)")
print(f"VALUES ('CGH', 'CGH-001', 'cgh@test.com', 'NYC', '{hospital_hash}', TRUE, TRUE, 'HOSPITAL');")
