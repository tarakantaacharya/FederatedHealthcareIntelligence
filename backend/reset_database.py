#!/usr/bin/env python
"""Reset database for testing - creates fresh schema and initial round."""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine, SessionLocal
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.model_weights import ModelWeights

# Drop all existing tables
print("Dropping existing tables...")
Base.metadata.drop_all(bind=engine)

# Create all tables
print("Creating fresh schema...")
Base.metadata.create_all(bind=engine)
print("OK - Database schema created successfully")

# Create initial round
db = SessionLocal()
try:
    round1 = TrainingRound(
        round_number=1,
        status=RoundStatus.OPEN,
        target_column="outcome",
        num_participating_hospitals=0,
        training_enabled=True
    )
    db.add(round1)
    db.commit()
    print("OK - Round 1 created with OPEN status")
    
    # Show state
    round_obj = db.query(TrainingRound).filter_by(round_number=1).first()
    print(f"  Round Number: {round_obj.round_number}")
    print(f"  Status: {round_obj.status}")
    print(f"  Started At: {round_obj.started_at}")
    
finally:
    db.close()
