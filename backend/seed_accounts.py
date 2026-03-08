#!/usr/bin/env python
"""Seed test admin and hospital accounts"""
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models.admin import Admin
from app.models.hospital import Hospital
from app.utils.security import hash_password
from sqlalchemy.exc import IntegrityError

db = SessionLocal()

try:
    # Check if admin exists
    existing_admin = db.query(Admin).filter(Admin.admin_id == 'ADMIN-001').first()
    if not existing_admin:
        admin = Admin(
            admin_id='ADMIN-001',
            admin_name='System Admin',
            contact_email='admin@central.local',
            hashed_password=hash_password('password'),
            role='ADMIN',
            is_active=True,
            is_super_admin=True
        )
        db.add(admin)
        db.flush()
        print("✓ Admin inserted successfully")
    else:
        print("✓ Admin already exists")
    
    # Insert test hospitals
    hospitals = [
        Hospital(
            hospital_name='Central General Hospital',
            hospital_id='CGH-001',
            contact_email='admin@cgh.local',
            location='Downtown',
            hashed_password=hash_password('TestHospital123!'),
            is_active=True,
            is_verified=True,
            role='HOSPITAL'
        ),
        Hospital(
            hospital_name='North Medical Center',
            hospital_id='NMC-001',
            contact_email='admin@nmc.local',
            location='North Side',
            hashed_password=hash_password('TestHospital123!'),
            is_active=True,
            is_verified=True,
            role='HOSPITAL'
        ),
        Hospital(
            hospital_name='East Community Hospital',
            hospital_id='ECH-001',
            contact_email='admin@ech.local',
            location='East Side',
            hashed_password=hash_password('TestHospital123!'),
            is_active=True,
            is_verified=True,
            role='HOSPITAL'
        )
    ]
    
    for hospital in hospitals:
        existing = db.query(Hospital).filter(Hospital.hospital_id == hospital.hospital_id).first()
        if not existing:
            db.add(hospital)
            db.flush()
            print(f"✓ Hospital {hospital.hospital_id} inserted successfully")
        else:
            print(f"✓ Hospital {hospital.hospital_id} already exists")
    
    db.commit()
    print("\n✅ All accounts seeded successfully!")
    
except IntegrityError as e:
    db.rollback()
    print(f"⚠️  Account already exists (skipping): {str(e)}")
    db.commit()
except Exception as e:
    db.rollback()
    print(f"❌ Error: {str(e)}")
finally:
    db.close()
