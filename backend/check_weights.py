#!/usr/bin/env python
"""Check model_weights table in detail"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.model_weights import ModelWeights

db = SessionLocal()

print('=== ALL MODEL_WEIGHTS ===')
all_mw = db.query(ModelWeights).order_by(ModelWeights.round_number.desc(), ModelWeights.created_at.desc()).all()
print(f'Total: {len(all_mw)}')

print('\n=== BY HOSPITAL_ID ===')
hospital_ids = set([w.hospital_id for w in all_mw])
for hid in sorted(hospital_ids):
    count = len([w for w in all_mw if w.hospital_id == hid])
    print(f'{hid}: {count} weights')

print('\n=== ROUNDS WITH GLOBAL MODELS ===')
rounds_with_global = {}
for w in all_mw:
    if w.hospital_id == 'GLOBAL' or w.model_type == 'global':
        if w.round_number not in rounds_with_global:
            rounds_with_global[w.round_number] = []
        rounds_with_global[w.round_number].append({
            'id': w.id,
            'hospital_id': w.hospital_id,
            'model_type': w.model_type if hasattr(w, 'model_type') else 'N/A',
            'hash': w.model_hash[:16] if w.model_hash else None,
            'created': w.created_at
        })

if rounds_with_global:
    for round_num in sorted(rounds_with_global.keys()):
        print(f'Round {round_num}: {rounds_with_global[round_num]}')
else:
    print('No global models found')

print('\n=== SAMPLE WEIGHTS (LAST 5) ===')
for w in all_mw[:5]:
    print(f'ID={w.id}, Round={w.round_number}, HospitalID={w.hospital_id}, Hash={w.model_hash[:16] if w.model_hash else None}..., Type={getattr(w, "model_type", "N/A")}')

db.close()
