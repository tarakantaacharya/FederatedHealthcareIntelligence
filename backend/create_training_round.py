"""Create active training round for testing"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound
from app.models.model_weights import ModelWeights

def create_round():
    db = SessionLocal()
    try:
        # Check if round exists
        existing = db.query(TrainingRound).filter(TrainingRound.round_number == 1).first()
        
        if existing:
            print(f"Round 1 already exists: status={existing.status}, target={existing.target_column}")
            # Update to in_progress with target_column
            existing.status = "in_progress"
            existing.target_column = "flu_cases"
            db.commit()
            print(f"Updated Round 1: status=in_progress, target_column=flu_cases")
        else:
            # Create new round
            new_round = TrainingRound(
                round_number=1,
                status="in_progress",
                target_column="flu_cases"
            )
            db.add(new_round)
            db.commit()
            print(f"Created Round 1: status=in_progress, target_column=flu_cases")
        
        # Verify
        round_check = db.query(TrainingRound).filter(TrainingRound.round_number == 1).first()
        print(f"\nVerification:")
        print(f"  Round number: {round_check.round_number}")
        print(f"  Status: {round_check.status}")
        print(f"  Target column: {round_check.target_column}")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_round()
