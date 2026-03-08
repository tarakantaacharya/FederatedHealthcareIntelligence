"""
Direct test of training service to see real traceback
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital
from app.services.training_service import TrainingService

def test_training_direct():
    db = SessionLocal()
    try:
        # Get test hospital
        hospital = db.query(Hospital).filter(Hospital.hospital_id == "CGH-001").first()
        if not hospital:
            print("ERROR: Hospital CGH-001 not found")
            return
        
        print(f"Found hospital: {hospital.hospital_id}")
        print(f"Testing training with dataset_id=1, target_column=flu_cases")
        print("="*70)
        
        # Call training service directly
        result = TrainingService.train_local_model(
            db=db,
            hospital=hospital,
            dataset_id=1,
            target_column="flu_cases",
            epochs=1,
            training_request=None
        )
        
        print("="*70)
        print("SUCCESS! Training completed")
        print(f"Result: {result}")
        
    except Exception as e:
        print("="*70)
        print(f"EXCEPTION CAUGHT: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("="*70)
        import traceback
        traceback.print_exc()
        print("="*70)
    finally:
        db.close()

if __name__ == "__main__":
    test_training_direct()
