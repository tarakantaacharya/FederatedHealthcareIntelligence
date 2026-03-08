#!/usr/bin/env python3
"""
End-to-end test for metrics flow
Tests: Training → Database → Aggregation → API Response
"""
import sys
sys.path.insert(0, '/d/federated-healthcare/federated-healthcare/backend')

from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session, sessionmaker
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.model_weights import ModelWeights
from app.services.training_service import TrainingService
from app.models.database import Base, engine as db_engine
import os
import pandas as pd

print("=" * 80)
print("COMPREHENSIVE METRICS END-TO-END TEST")
print("=" * 80)

# Create session
SessionLocal = sessionmaker(bind=db_engine)
db = SessionLocal()

try:
    # Check 1: Verify round exists
    print("\n[1] Checking for active training round...")
    round_record = db.query(TrainingRound).filter(
        TrainingRound.status == RoundStatus.TRAINING
    ).first()
    
    if not round_record:
        print("❌ No TRAINING round found")
        sys.exit(1)
    
    print(f"✓ Found round {round_record.round_number}, target: {round_record.target_column}")
    
    # Check 2: Get a hospital with a dataset
    print("\n[2] Finding hospital with dataset...")
    hospital = db.query(Hospital).filter(Hospital.is_active == True).first()
    if not hospital:
        print("❌ No active hospital found")
        sys.exit(1)
    
    dataset = db.query(Dataset).filter(Dataset.hospital_id == hospital.id).first()
    if not dataset:
        print(f"❌ Hospital {hospital.hospital_id} has no datasets")
        sys.exit(1)
    
    print(f"✓ Hospital: {hospital.hospital_id}, Dataset: {dataset.file_path}")
    
    # Check 3: Verify dataset file exists
    if not os.path.exists(dataset.file_path):
        print(f"❌ Dataset file not found: {dataset.file_path}")
        sys.exit(1)
    
    df = pd.read_csv(dataset.file_path)
    print(f"✓ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"  Columns: {', '.join(df.columns[:5])}...")
    
    # Check 4: Run training
    print(f"\n[3] Starting training for hospital {hospital.hospital_id}...")
    print("    This will take a moment...")
    
    training_result = TrainingService.train_local_model(
        db=db,
        hospital=hospital,
        dataset_id=dataset.id,
        target_column=round_record.target_column,
        epochs=3,  # Reduced for faster testing
        lr=0.001,
        max_grad_norm=1.0,
        noise_multiplier=1.1,
        epsilon_budget=5.0
    )
    
    print(f"✓ Training complete")
    print(f"  Model ID: {training_result['model_id']}")
    print(f"  Train loss: {training_result['train_loss']:.4f}")
    print(f"  Epsilon spent: {training_result['epsilon_spent']:.6f}")
    
    # Check 5: Verify metrics in training result
    print(f"\n[4] Metrics in training result:")
    metrics = training_result.get('metrics', {})
    print(f"  MAPE: {metrics.get('mape', 'N/A')}")
    print(f"  RMSE: {metrics.get('rmse', 'N/A')}")
    print(f"  R2: {metrics.get('r2', 'N/A')}")
    print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
    
    # Check 6: Query database for saved metrics
    print(f"\n[5] Checking database for metrics...")
    model = db.query(ModelWeights).filter(
        ModelWeights.id == training_result['model_id']
    ).first()
    
    if not model:
        print("❌ Model not found in database")
        sys.exit(1)
    
    print(f"✓ Model found in DB:")
    print(f"  Local Loss: {model.local_loss}")
    print(f"  Local Accuracy: {model.local_accuracy}")
    print(f"  Local MAPE: {model.local_mape} ← CHECK: Should have value")
    print(f"  Local RMSE: {model.local_rmse} ← CHECK: Should have value")
    print(f"  Local R2: {model.local_r2} ← CHECK: Should have value")
    
    if model.local_mape is None:
        print("\n⚠ PROBLEM: local_mape is still NULL")
        print("  This means the fallback mechanism isn't working")
    else:
        print("\n✓ SUCCESS: Metrics are being saved!")
    
    # Check 7: Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Training result metrics: {metrics}")
    print(f"Database metrics: MAPE={model.local_mape}, RMSE={model.local_rmse}, R2={model.local_r2}")
    
    if all([model.local_mape is not None, model.local_rmse is not None, model.local_r2 is not None]):
        print("\n✓✓✓ ALL METRICS BEING SAVED ✓✓✓")
    else:
        print("\n✗✗✗ METRICS NOT BEING SAVED ✗✗✗")
        print("\nNext step: Check backend logs for [METRICS-*] messages")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
    print("\n" + "=" * 80)
