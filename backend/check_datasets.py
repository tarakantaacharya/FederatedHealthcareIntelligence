"""
Check what datasets exist
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital
from app.models.dataset import Dataset

def check_datasets():
    db = SessionLocal()
    try:
        # Get test hospital
        hospital = db.query(Hospital).filter(Hospital.hospital_id == "CGH-001").first()
        if not hospital:
            print("ERROR: Hospital CGH-001 not found")
            return
        
        print(f"Hospital: {hospital.hospital_id} (id={hospital.id})")
        
        # Get all datasets for this hospital
        datasets = db.query(Dataset).filter(Dataset.hospital_id == hospital.id).all()
        print(f"\nDatasets for this hospital:")
        for ds in datasets:
            print(f"  - id={ds.id}, filename={ds.filename}, file_path={ds.file_path}")
        
        # Get dataset with id=2
        dataset2 = db.query(Dataset).filter(Dataset.id == 2).first()
        if dataset2:
            print(f"\nDataset id=2: hospital_id={dataset2.hospital_id}, filename={dataset2.filename}")
        else:
            print(f"\nDataset id=2: NOT FOUND")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_datasets()
