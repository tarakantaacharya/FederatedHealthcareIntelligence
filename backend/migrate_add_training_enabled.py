"""
Migration: Add training_enabled column to training_rounds table
Run this once to update existing database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.database import engine

def migrate():
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('training_rounds') 
                WHERE name='training_enabled'
            """))
            
            exists = result.fetchone()[0] > 0
            
            if exists:
                print("✅ Column 'training_enabled' already exists")
                return
            
            # Add column with default value True
            conn.execute(text("""
                ALTER TABLE training_rounds 
                ADD COLUMN training_enabled BOOLEAN DEFAULT 1 NOT NULL
            """))
            conn.commit()
            
            print("✅ Migration complete: training_enabled column added")
            print("   All existing rounds have training_enabled=True by default")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
