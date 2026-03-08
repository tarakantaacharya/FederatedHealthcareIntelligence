"""Check dataset columns"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.hospital import Hospital  # Need this for relationship

def check_columns():
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == 1).first()
        if not dataset:
            print("Dataset not found")
            return
        
        print(f"Dataset: {dataset.filename}")
        print(f"File path: {dataset.file_path}")
        
        df = pd.read_csv(dataset.file_path)
        print(f"\nColumns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        print(f"\nFirst few rows:")
        print(df.head())
    finally:
        db.close()

if __name__ == "__main__":
    check_columns()
