#!/usr/bin/env python
"""Verify hospitals_profile table has new columns"""
from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///../data/federated.db')
inspector = inspect(engine)

print('=== hospitals_profile table columns ===')
cols = inspector.get_columns('hospitals_profile')
for col in cols:
    print(f"  {col['name']}: {col['type']}")

# Check for new fields
col_names = [c['name'] for c in cols]
print(f"\n✓ size_category present: {'size_category' in col_names}")
print(f"✓ experience_level present: {'experience_level' in col_names}")
print(f"✓ Total columns: {len(col_names)}")
