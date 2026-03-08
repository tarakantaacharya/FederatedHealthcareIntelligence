"""Check active rounds"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.hospital import Hospital  # Import all related models
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound

def check_rounds():
    db = SessionLocal()
    try:
        rounds = db.query(TrainingRound).all()
        print(f"Total rounds: {len(rounds)}")
        for r in rounds:
            print(f"  Round {r.round_number}: status={r.status}, target={r.target_column}")
        
        active = db.query(TrainingRound).filter(TrainingRound.status == 'active').first()
        if active:
            print(f"\nActive round: Round {active.round_number}, target_column={active.target_column}")
        else:
            print(f"\nNo active round found")
    finally:
        db.close()

if __name__ == "__main__":
    check_rounds()
