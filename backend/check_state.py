#!/usr/bin/env python
"""Check database state"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.training_rounds import TrainingRound
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital

db = SessionLocal()

print('=== DATABASE STATE ===')
print(f'Hospitals: {db.query(Hospital).count()}')
print(f'Training Rounds: {db.query(TrainingRound).count()}')
print(f'Model Weights: {db.query(ModelWeights).count()}')

print('\n=== TRAINING ROUNDS ===')
rounds = db.query(TrainingRound).all()
if rounds:
    for r in rounds:
        print(f'Round {r.round_number}: status={r.status}')
else:
    print('No rounds in database')

print('\n=== GLOBAL MODELS ===')
globals_mw = db.query(ModelWeights).filter(ModelWeights.hospital_id == 'GLOBAL').all()
if globals_mw:
    for g in globals_mw:
        print(f'Round {g.round_number}: hash={g.model_hash[:16] if g.model_hash else None}..., created={g.created_at}')
else:
    print('No global models')

print('\n=== LATEST MODEL ===')
latest = db.query(ModelWeights).filter(ModelWeights.hospital_id == 'GLOBAL').order_by(ModelWeights.created_at.desc()).first()
if latest:
    print(f'Round {latest.round_number}: hash={latest.model_hash[:32] if latest.model_hash else None}...')
else:
    print('No latest global model')

db.close()
