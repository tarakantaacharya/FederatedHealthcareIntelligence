"""Debug weight upload - direct service call"""
from app.database import SessionLocal
from app.models.hospital import Hospital
from app.services.weight_service import WeightService
import traceback

db = SessionLocal()

#  Get hospital
hospital = db.query(Hospital).filter(Hospital.hospital_id == 'AYURVEDA').first()
print(f"Hospital: {hospital.hospital_name} (ID: {hospital.id})")

# Try to upload weights
try:
    print("\n=== Attempting weight upload ===")
    result = WeightService.upload_weights_to_central(
        model_id=5,
        db=db,
        hospital=hospital,
        round_number=1,
        actual_hyperparameters={
            "epochs": 5,
            "batch_size": 32,
            "learning_rate": 0.001
        }
    )
    print("\n✅ SUCCESS!")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

finally:
    db.close()
