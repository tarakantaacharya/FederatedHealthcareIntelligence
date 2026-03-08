from app.database import SessionLocal
from app.models.hospital import Hospital
from app.utils.security import verify_password

db = SessionLocal()
hospital = db.query(Hospital).filter(Hospital.hospital_id == 'CGH-001').first()
if hospital:
    print(f'Hospital found: {hospital.hospital_name}')
    print(f'Password hash starts with: {hospital.hashed_password[:30]}...')
    # Test password verification
    test_passwords = ['hospital123', 'cghadmin123', 'TestHospital123!', 'cghpass123']
    for pwd in test_passwords:
        result = verify_password(pwd, hospital.hashed_password)
        print(f'Password "{pwd}": {result}')
else:
    print('Hospital not found')
db.close()
