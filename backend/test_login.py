"""Test login directly"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital
from app.utils.security import pwd_context

def test_login():
    db = SessionLocal()
    try:
        hospital = db.query(Hospital).filter(Hospital.hospital_id == "CGH-001").first()
        if not hospital:
            print("Hospital CGH-001 not found")
            return
        
        print(f"Hospital: {hospital.hospital_id}")
        print(f"Name: {hospital.hospital_name}")
        print(f"Password hash: {hospital.hashed_password[:50]}...")
        
        # Test various passwords
        passwords = ["hospital123", "CGH_Password_001", "TestHospital123!", "CGH-001"]
        
        for pwd in passwords:
            result = pwd_context.verify(pwd, hospital.hashed_password)
            print(f"\nPassword '{pwd}': {result}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_login()
