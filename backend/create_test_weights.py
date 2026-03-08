"""Create test ModelWeights data for Round 2"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound
from datetime import datetime

db = SessionLocal()

try:
    # Get Round 2
    round_2 = db.query(TrainingRound).filter(TrainingRound.round_number == 2).first()
    if not round_2:
        print("Round 2 not found")
        exit(1)
    
    print(f"Found Round 2: {round_2.round_number}")
    
    # Get hospitals
    hospitals = db.query(Hospital).all()
    print(f"Found {len(hospitals)} hospitals")
    
    # Create ModelWeights for each hospital
    for hospital in hospitals:
        # Check if already exists
        existing = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital.id,
            ModelWeights.round_number == 2
        ).first()
        
        if not existing:
            mw = ModelWeights(
                hospital_id=hospital.id,
                dataset_id=None,  # NULL since we're not using datasets
                round_number=2,
                round_id=round_2.id,
                model_path=f"/storage/models/round_2/hospital_{hospital.id}.pkl",
                model_type="sklearn_baseline",
                local_loss=0.45 + (hospital.id * 0.05),
                local_accuracy=0.80 - (hospital.id * 0.05),
                is_global=False,
                is_uploaded=True,
                is_mask_uploaded=True,
                model_hash="test_hash",
                created_at=datetime.now()
            )
            db.add(mw)
            print(f"✓ Created ModelWeights for {hospital.hospital_name}")
        else:
            print(f"⊘ ModelWeights already exists for {hospital.hospital_name}")
    
    db.commit()
    print("✓ Saved to database")
    
finally:
    db.close()
