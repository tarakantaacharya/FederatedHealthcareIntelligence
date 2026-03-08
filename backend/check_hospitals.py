"""Check hospital credentials"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital

def check_hospitals():
    db = SessionLocal()
    try:
        hospitals = db.query(Hospital).all()
        print(f"Total hospitals: {len(hospitals)}")
        for h in hospitals:
            print(f"  - hospital_id: {h.hospital_id}, name: {h.hospital_name}, id: {h.id}")
    finally:
        db.close()

if __name__ == "__main__":
    check_hospitals()
