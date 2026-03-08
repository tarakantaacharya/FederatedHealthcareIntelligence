#!/usr/bin/env python
"""
Minimal test to reproduce tuple detach error with TFT
Tests forward pass and loss computation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import torch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer

print("=" * 70)
print("MINIMAL TFT + PyTorch 2.1 Test")
print("=" * 70)

# Create sample data
n_samples = 200
data = {
    'time_idx': range(n_samples),
    'group_id': ['hospital'] * n_samples,  # Add group identifier
    'bed_occupancy': np.sin(np.arange(n_samples) / 10) * 50 + 50 + np.random.normal(0, 5, n_samples),
    'feature1': np.random.randn(n_samples),
}
df = pd.DataFrame(data)

print(f"\n[1] Created dataset: {df.shape}")

# Create TimeSeriesDataSet
training_cutoff = int(n_samples * 0.8)

dataset = TimeSeriesDataSet(
    df[lambda x: x.time_idx <= training_cutoff],
    time_idx='time_idx',
    target='bed_occupancy',
    group_ids=['group_id'],  # Fixed: add group
    min_encoder_length=24,
    max_encoder_length=24,
    min_prediction_length=3,
    max_prediction_length=3,
    static_categoricals=['group_id'],
    static_reals=[],
    time_varying_known_categoricals=[],
    time_varying_known_reals=[],
    time_varying_unknown_categoricals=[],
    time_varying_unknown_reals=['feature1'],
    target_normalizer=GroupNormalizer(groups=['group_id']),
    add_relative_time_idx=True,
    add_target_scales=True,
    allow_missing_timesteps=False
)

print(f"[2] Created TimeSeriesDataSet")

# Create dataloader
dataloader = dataset.to_dataloader(
    train=True,
    batch_size=16,
    num_workers=0,
    shuffle=False
)

print(f"[3] Created DataLoader")

# Create model
model = TemporalFusionTransformer.from_dataset(
    dataset,
    learning_rate=0.001,
    hidden_size=32,
    attention_head_size=2,
    dropout=0.1,
    output_size=3
)

print(f"[4] Created TFT model")

device = torch.device("cpu")
model = model.to(device)
model.train()

print(f"[5] Model moved to {device}")

# Test forward pass
print("\n[TEST] Running forward pass and loss computation...")
try:
    for batch_idx, batch in enumerate(dataloader):
        print(f"\n  Batch {batch_idx+1}:")
        x, y = batch
        print(f"    x type: {type(x)}")
        print(f"    y type: {type(y)}, shape: {y[0].shape if isinstance(y, tuple) else y.shape}")
        
        print(f"    Running model(x)...")
        output = model(x)
        print(f"    Output type: {type(output)}, is tuple: {isinstance(output, tuple)}")
        
        if isinstance(output, tuple):
            predictions = output[0]
            print(f"    Predictions extracted from tuple, shape: {predictions.shape}")
        else:
            predictions = output
            print(f"    Predictions shape: {predictions.shape}")
        
        print(f"    Computing loss...")
        loss = model.loss(predictions, y)
        print(f"    Loss type: {type(loss)}, is tuple: {isinstance(loss, (tuple, list))}")
        
        if isinstance(loss, (tuple, list)):
            print(f"    Loss is tuple/list, elements: {[type(l) for l in loss]}")
            loss = torch.mean(torch.stack([torch.as_tensor(l) for l in loss]))
            print(f"    Loss converted to tensor: {loss}")
        
        print(f"    Loss value: {loss.item()}")
        
        print(f"    Running loss.backward()...")
        loss.backward()
        
        print(f"    ✓ Batch {batch_idx+1} succeeded!")
        
        if batch_idx >= 2:  # Test first 3 batches
            break
            
    print("\n" + "=" * 70)
    print("SUCCESS: No tuple detach errors!")
    print("=" * 70)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
