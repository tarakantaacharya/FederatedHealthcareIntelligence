#!/usr/bin/env python3
"""
Diagnostic script to trace metric flow through training and aggregation
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Connect to database
engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')

print("=" * 80)
print("METRICS DIAGNOSTIC REPORT")
print("=" * 80)

# Check current data
with engine.connect() as conn:
    # Check round 2 status
    print("\n[ROUND DATA]")
    result = conn.execute(text("""
        SELECT 
            id, round_number, status, 
            average_loss, average_accuracy, average_mape, average_rmse, average_r2
        FROM training_rounds 
        WHERE round_number = 2
    """))
    row = result.fetchone()
    if row:
        print(f"Round ID: {row[0]}")
        print(f"Round #: {row[1]}")
        print(f"Status: {row[2]}")
        print(f"AVG Loss: {row[3]}")
        print(f"AVG Accuracy: {row[4]}")
        print(f"AVG MAPE: {row[5]} (PROBLEM: should be computed)")
        print(f"AVG RMSE: {row[6]} (PROBLEM: should be computed)")
        print(f"AVG R2: {row[7]} (PROBLEM: should be computed)")
    else:
        print("No round 2 found")

# Check hospital models for round 2
print("\n[HOSPITAL TRAINING METRICS - Round 2]")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            m.id, m.hospital_id, m.round_number,
            m.local_loss, m.local_accuracy, m.local_mape, m.local_rmse, m.local_r2,
            m.is_uploaded, m.is_mask_uploaded, m.is_global
        FROM model_weights m
        WHERE m.round_number = 2 AND m.is_global = 0
        ORDER BY m.hospital_id
    """))
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"\nModel ID: {row[0]}, Hospital: {row[1]}")
            print(f"  Loss: {row[3]} (Present: {'✓' if row[3] is not None else '✗'})")
            print(f"  Accuracy: {row[4]} (Present: {'✓' if row[4] is not None else '✗'})")
            print(f"  MAPE: {row[5]} ← PROBLEM: None/NULL")
            print(f"  RMSE: {row[6]} ← PROBLEM: None/NULL")
            print(f"  R2: {row[7]} ← PROBLEM: None/NULL")
            print(f"  Uploaded: {row[8]}, Mask: {row[9]}")
    else:
        print("No hospital models for round 2")

# Check the global model for round 2
print("\n[GLOBAL MODEL - Round 2]")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            m.id, m.hospital_id, m.is_global,
            m.local_loss, m.local_accuracy, m.local_mape, m.local_rmse, m.local_r2,
            m.model_path
        FROM model_weights m
        WHERE m.round_number = 2 AND m.is_global = 1
    """))
    row = result.fetchone()
    if row:
        print(f"Model ID: {row[0]}, Hospital: {row[1]}, Global: {row[2]}")
        print(f"  Loss: {row[3]} (Present: {'✓' if row[3] is not None else '✗'}) ← Should have avg_loss")
        print(f"  Accuracy: {row[4]} (Present: {'✓' if row[4] is not None else '✗'}) ← Should have avg_accuracy")
        print(f"  MAPE: {row[5]} ← PROBLEM: None/NULL")
        print(f"  RMSE: {row[6]} ← PROBLEM: None/NULL")
        print(f"  R2: {row[7]} ← PROBLEM: None/NULL")
        print(f"  Path: {row[8]}")
    else:
        print("No global model for round 2")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)
print("""
FINDING: local_mape, local_rmse, local_r2 are NULL in database

POSSIBLE CAUSES:
1. Training service not computing metrics (metrics computation failing)
2. Training service computing metrics but not saving them (bug in DB save)
3. Metrics computed as 0.0 but fallback not working
4. Database transaction not committing the values

ACTION ITEMS:
1. Check training logs to see what metrics are computed
2. Verify training_service.py actually sets these fields
3. Run new training with detailed logging
4. Check if fallback metrics logic is working
""")
