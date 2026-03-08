#!/usr/bin/env python
"""
Add Phase B Dataset Intelligence columns to datasets table
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()

def migrate_database():
    """Add missing Dataset columns"""
    print(" Adding Phase B Dataset Intelligence columns...")
    
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(datasets)"))
        existing_columns = {row[1] for row in result}
        print(f"Existing columns: {existing_columns}")
        
        columns_to_add = [
            ("times_trained", "INTEGER DEFAULT 0"),
            ("times_federated", "INTEGER DEFAULT 0"),
            ("last_trained_at", "DATETIME"),
            ("involved_rounds", "TEXT"),  # JSON column (SQLite uses TEXT for JSON)
            ("last_training_type", "VARCHAR(20)"),
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"✓ Adding column: {column_name}")
                try:
                    conn.execute(text(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                except Exception as e:
                    print(f"✗ Failed to add {column_name}: {e}")
            else:
                print(f"- Column {column_name} already exists, skipping")
        
        # Verify the migration
        print("\n☑ Verification - Final schema:")
        result = conn.execute(text("PRAGMA table_info(datasets)"))
        for row in result:
            print(f"  {row[1]}: {row[2]}")
    
    print(f"\n✅ Migration complete!")

if __name__ == "__main__":
    migrate_database()
