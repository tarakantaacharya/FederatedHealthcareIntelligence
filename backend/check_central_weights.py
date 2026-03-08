#!/usr/bin/env python3
"""
Check central weights storage for metrics
"""
import json
import os
from pathlib import Path

CENTRAL_DIR = "storage/models/central"

print("=" * 80)
print("CENTRAL WEIGHTS STORAGE - METRICS CHECK")
print("=" * 80)

# List all round directories
if os.path.exists(CENTRAL_DIR):
    rounds = sorted([d for d in os.listdir(CENTRAL_DIR) if d.startswith('round_')])
    
    for round_name in rounds[-2:]:  # Check last 2 rounds
        round_path = os.path.join(CENTRAL_DIR, round_name)
        weights_files = [f for f in os.listdir(round_path) if f.startswith('weights_')]
        
        print(f"\n{round_name.upper()}:")
        print("-" * 80)
        
        for weights_file in weights_files:
            file_path = os.path.join(round_path, weights_file)
            print(f"\nFile: {weights_file}")
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check if metadata has metrics
                metadata = data.get('metadata', {})
                print(f"  Metadata keys: {list(metadata.keys())}")
                
                # Check for metric fields
                metrics_fields = ['local_mape', 'local_rmse', 'local_r2']
                for metric in metrics_fields:
                    value = metadata.get(metric)
                    status = "✓" if value is not None else "✗"
                    print(f"    {status} {metric}: {value}")
                
                # Show weights summary
                weights = data.get('weights', {})
                print(f"  Weights summary:")
                print(f"    Total keys: {len(weights)}")
                if weights:
                    first_key = list(weights.keys())[0]
                    print(f"    Sample: {first_key} = {weights[first_key]}")
                    
            except Exception as e:
                print(f"  Error reading file: {e}")
else:
    print(f"\nCentral directory not found at {CENTRAL_DIR}")

print("\n" + "=" * 80)
print("To find the full path:")
print(f"import os; print(os.path.abspath('{CENTRAL_DIR}'))")
print("=" * 80)
