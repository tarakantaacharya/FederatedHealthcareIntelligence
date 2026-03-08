#!/usr/bin/env python
"""
Integration test for training endpoint
Tests that the training pipeline works with sklearn baseline (no TFT)
"""
import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all critical modules import without PyTorch errors"""
    print("=" * 60)
    print("TEST 1: Checking critical imports...")
    print("=" * 60)
    
    try:
        print("  • Importing FastAPI app...")
        from app.main import app
        print("    ✓ app.main imported")
        
        print("  • Importing TrainingService...")
        from app.services.training_service import TrainingService
        print("    ✓ TrainingService imported")
        
        print("  • Importing PredictionService...")
        from app.services.prediction_service import PredictionService
        print("    ✓ PredictionService imported")
        
        print("  • Importing WeightService...")
        from app.services.weight_service import WeightService
        print("    ✓ WeightService imported")
        
        print("  • Importing BaselineForecaster...")
        from app.ml.baseline_model import BaselineForecaster
        print("    ✓ BaselineForecaster imported")
        
        print("\n✅ TEST 1 PASSED: All imports successful\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_baseline_forecaster():
    """Test that BaselineForecaster can be instantiated and trained"""
    print("=" * 60)
    print("TEST 2: Testing BaselineForecaster...")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from app.ml.baseline_model import BaselineForecaster
        
        print("  • Creating sample dataset...")
        # Create a simple time series dataset
        dates = pd.date_range('2024-01-01', periods=100, freq='h')
        data = {
            'timestamp': dates,
            'bed_occupancy': np.sin(np.arange(100) / 10) * 50 + 50 + np.random.normal(0, 5, 100),
            'staff_capacity': np.random.randint(80, 95, 100),
        }
        df = pd.DataFrame(data)
        print(f"    ✓ Dataset created: {df.shape[0]} rows, columns: {list(df.columns)}")
        
        print("  • Instantiating BaselineForecaster...")
        forecaster = BaselineForecaster(target_column='bed_occupancy')
        print("    ✓ BaselineForecaster instantiated")
        
        print("  • Training model...")
        metrics = forecaster.train(df)
        print(f"    ✓ Model trained")
        
        print("  • Checking metrics...")
        required_keys = ['train_loss', 'train_mse', 'train_mae', 'train_r2']
        for key in required_keys:
            if key in metrics:
                print(f"    ✓ {key}: {metrics[key]:.4f}")
            else:
                print(f"    ✗ Missing metric: {key}")
                return False
        
        print("\n✅ TEST 2 PASSED: BaselineForecaster works correctly\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_tft_availability():
    """Test that TFT is properly disabled"""
    print("=" * 60)
    print("TEST 3: Verifying TFT is disabled...")
    print("=" * 60)
    
    try:
        from app.services.training_service import TFT_AVAILABLE as training_tft
        from app.services.weight_service import TFT_AVAILABLE as weight_tft
        from app.services.prediction_service import TFT_AVAILABLE as pred_tft
        
        print(f"  • TrainingService.TFT_AVAILABLE = {training_tft}")
        print(f"  • WeightService.TFT_AVAILABLE = {weight_tft}")
        print(f"  • PredictionService.TFT_AVAILABLE = {pred_tft}")
        
        if training_tft or weight_tft or pred_tft:
            print("\n❌ TEST 3 FAILED: TFT should be disabled everywhere")
            return False
        
        print("\n✅ TEST 3 PASSED: TFT is properly disabled\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  TRAINING PIPELINE INTEGRATION TESTS".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("BaselineForecaster", test_baseline_forecaster()))
    results.append(("TFT Disabled", test_tft_availability()))
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:.<40} {status}")
    
    print()
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("╔" + "=" * 58 + "╗")
        print("║" + "  ✅ ALL TESTS PASSED  ✅".center(58) + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("The training pipeline is ready for HTTP requests.")
        print("No PyTorch detach errors detected.")
        return 0
    else:
        print("╔" + "=" * 58 + "╗")
        print("║" + "  ❌ SOME TESTS FAILED  ❌".center(58) + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
