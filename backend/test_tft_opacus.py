#!/usr/bin/env python
"""Test TFT + Opacus import after fixes"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("TESTING TFT + OPACUS DP-SGD IMPLEMENTATION")
print("=" * 70)

try:
    print("\n[1/4] Importing app.main...")
    from app.main import app
    print("✓ FastAPI app imported successfully")
    
    print("\n[2/4] Importing TrainingService...")
    from app.services.training_service import TrainingService, TFT_AVAILABLE
    print(f"✓ TrainingService imported (TFT_AVAILABLE={TFT_AVAILABLE})")
    
    print("\n[3/4] Importing TFT components...")
    from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
    from pytorch_forecasting.metrics import QuantileLoss
    from opacus import PrivacyEngine
    print("✓ TFT and Opacus components imported successfully")
    
    print("\n[4/4] Verifying training method exists...")
    assert hasattr(TrainingService, 'train_local_model')
    assert hasattr(TrainingService, '_prepare_timeseries_data')
    print("✓ TrainingService methods verified")
    
    print("\n" + "=" * 70)
    print("✅ ALL IMPORTS SUCCESSFUL - TFT + DP-SGD Ready")
    print("=" * 70)
    print("\nArchitecture:")
    print("  • Model: TemporalFusionTransformer (3-horizon output)")
    print("  • DP: Opacus PrivacyEngine with DP-SGD")
    print("  • Training: Manual PyTorch loop with tuple handling")
    print("  • Privacy: Epsilon accounting after training")
    print("=" * 70 + "\n")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ IMPORT FAILED: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
