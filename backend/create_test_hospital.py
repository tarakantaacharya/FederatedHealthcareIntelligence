#!/usr/bin/env python
from app.models.hospital import Hospital
from app.database import SessionLocal
from app.utils.security import pwd_context

db = SessionLocal()

# Check if hospital exists
existing = db.query(Hospital).filter(Hospital.hospital_id == 'CGH-001').first()
if existing:
    print(f"Hospital {existing.hospital_id} already exists")
else:
    # Create hospital
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
    print("Hospital CGH-001 created successfully")

db.close()
