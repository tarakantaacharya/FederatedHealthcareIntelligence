#!/usr/bin/env python
"""
Test script to verify app imports without TFT errors
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("=== Testing app import ===")
try:
    print("Step 1: Import app.main...")
    from app.main import app
    print("✓ Step 1 PASSED: app.main imported successfully")
    
    print("Step 2: Check app routes...")
    print(f"✓ App routes registered: {len(app.routes)} routes")
    
    print("Step 3: Test training service...")
    from app.services.training_service import TrainingService
    print("✓ Step 3 PASSED: TrainingService imported successfully")
    
    print("Step 4: Test prediction service...")
    from app.services.prediction_service import PredictionService
    print("✓ Step 4 PASSED: PredictionService imported successfully")
    
    print("\n✅ ALL IMPORTS SUCCESSFUL - No PyTorch detach errors!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ IMPORT FAILED: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
