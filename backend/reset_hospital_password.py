#!/usr/bin/env python
"""Reset CGH-001 password"""
from app.models.hospital import Hospital
from app.database import SessionLocal
from app.utils.security import pwd_context

db = SessionLocal()

# Find hospital
hospital = db.query(Hospital).filter(Hospital.hospital_id == 'CGH-001').first()
if not hospital:
    print("Hospital CGH-001 not found. Creating...")
    hospital = Hospital(
        hospital_id='CGH-001',
        hospital_name='City General Hospital',
        contact_email='cgh@test.com',
        location='New York',
        hashed_password=pwd_context.hash('hospital123'),
        role='HOSPITAL'
    )
    db.add(hospital)
    db.commit()
    print("Hospital CGH-001 created with password: hospital123")
else:
    # Reset password
    hospital.hashed_password = pwd_context.hash('hospital123')
    db.commit()
    print(f"Password reset for hospital {hospital.hospital_id}")
    print(f"Hospital ID: CGH-001")
    print(f"Password: hospital123")
    print(f"Name: {hospital.hospital_name}")
    print(f"Email: {hospital.contact_email}")

db.close()
