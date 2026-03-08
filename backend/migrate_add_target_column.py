#!/usr/bin/env python
"""
Quick migration script to add target_column to training_rounds table
"""
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

try:
    with engine.connect() as conn:
        # Try to add the column
        conn.execute(text('ALTER TABLE training_rounds ADD COLUMN target_column VARCHAR(255) NOT NULL'))
        conn.commit()
        print('✓ Added target_column to training_rounds table')
except Exception as e:
    if 'Duplicate column name' in str(e):
        print('✓ target_column already exists')
    else:
        print(f'Error: {e}')
finally:
    engine.dispose()
