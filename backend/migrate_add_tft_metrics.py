"""
Migration: Add TFT metrics columns to model_weights table
Phase: 20+ (TFT metrics tracking)
Date: 2026-02-26
"""

import sys
import os

# Ensure we're in the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text, inspect
from app.config import get_settings

# Get settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

def run_migration():
    """Add local_mape, local_rmse, local_r2 columns to model_weights"""
    
    with engine.connect() as conn:
        # Get current table schema
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('model_weights')]
        
        print("✓ Current model_weights columns:")
        for col in sorted(columns):
            print(f"  - {col}")
        
        # Check which columns are missing
        missing_columns = []
        if 'local_mape' not in columns:
            missing_columns.append('local_mape')
        if 'local_rmse' not in columns:
            missing_columns.append('local_rmse')
        if 'local_r2' not in columns:
            missing_columns.append('local_r2')
        if 'round_id' not in columns:
            missing_columns.append('round_id')
        if 'is_uploaded' not in columns:
            missing_columns.append('is_uploaded')
        if 'is_mask_uploaded' not in columns:
            missing_columns.append('is_mask_uploaded')
        if 'weights_hash' not in columns:
            missing_columns.append('weights_hash')
        if 'dataset_id' not in columns:
            missing_columns.append('dataset_id')
        
        if not missing_columns:
            print("\n✓ All columns already exist!")
            return True
        
        print(f"\n✗ Missing columns: {', '.join(missing_columns)}")
        print("\nAdding missing columns...")
        
        # Add each missing column
        if 'local_mape' not in columns:
            print("  + Adding local_mape...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN local_mape FLOAT NULL"))
            conn.commit()
        
        if 'local_rmse' not in columns:
            print("  + Adding local_rmse...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN local_rmse FLOAT NULL"))
            conn.commit()
        
        if 'local_r2' not in columns:
            print("  + Adding local_r2...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN local_r2 FLOAT NULL"))
            conn.commit()
        
        if 'dataset_id' not in columns:
            print("  + Adding dataset_id...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN dataset_id INT NULL"))
            conn.commit()
        
        if 'round_id' not in columns:
            print("  + Adding round_id...")
            conn.execute(text("""
                ALTER TABLE model_weights 
                ADD COLUMN round_id INT NULL,
                ADD FOREIGN KEY (round_id) REFERENCES training_rounds(id)
            """))
            conn.commit()
        
        if 'is_uploaded' not in columns:
            print("  + Adding is_uploaded...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN is_uploaded BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        if 'is_mask_uploaded' not in columns:
            print("  + Adding is_mask_uploaded...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN is_mask_uploaded BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        if 'weights_hash' not in columns:
            print("  + Adding weights_hash...")
            conn.execute(text("ALTER TABLE model_weights ADD COLUMN weights_hash VARCHAR(128) NULL"))
            conn.commit()
        
        # Add updated_at if missing
        if 'updated_at' not in columns:
            print("  + Adding updated_at...")
            conn.execute(text("""
                ALTER TABLE model_weights 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """))
            conn.commit()
        
        print("\n✓ Migration completed successfully!")
        
        # Verify
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('model_weights')]
        print(f"\n✓ Final model_weights columns ({len(columns)} total):")
        for col in sorted(columns):
            print(f"  - {col}")
        
        return True

if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
