import sys
sys.path.insert(0, '.')

# Import the module and check
import app.ml.tft_forecaster as tft_mod

print(f"PYTORCH_AVAILABLE = {tft_mod.PYTORCH_AVAILABLE}")
print(f"Has TimeSeriesDataSet = {hasattr(tft_mod, 'TimeSeriesDataSet')}")
print(f"TimeSeriesDataSet is Any = {str(tft_mod.TimeSeriesDataSet)}")

# Try importing again
try:
    import torch
    import pytorch_forecasting
    from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
    print("Direct imports work!")
except Exception as e:
    print(f"Direct imports failed: {e}")
