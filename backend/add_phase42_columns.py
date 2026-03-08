#!/usr/bin/env python
"""Add Phase 42 columns to MySQL database directly"""
import sys
from sqlalchemy import text
from app.database import engine

def add_columns():
    """Add missing Phase 42 columns to database"""
    
    with engine.connect() as connection:
        try:
            # Add columns to model_weights
            print("Adding columns to model_weights table...")
            
            # Check if column already exists before adding
            columns_to_add = [
                ("actual_hyperparameters", "ALTER TABLE model_weights ADD COLUMN actual_hyperparameters JSON NULL DEFAULT NULL COMMENT 'Actual hyperparameters used during training'"),
                ("hyperparameter_compliant", "ALTER TABLE model_weights ADD COLUMN hyperparameter_compliant BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Whether model complies with federated contract hyperparameters'"),
            ]
            
            for col_name, sql in columns_to_add:
                try:
                    connection.execute(text(sql))
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"  ℹ️  Column already exists: {col_name}")
                    else:
                        print(f"  ❌ Error adding {col_name}: {e}")
            
            # Add columns to training_rounds
            print("\nAdding columns to training_rounds table...")
            
            round_columns = [
                ("tft_hidden_size", "ALTER TABLE training_rounds ADD COLUMN tft_hidden_size INT NULL DEFAULT NULL COMMENT 'TFT hidden dimension for embedding'"),
                ("tft_attention_heads", "ALTER TABLE training_rounds ADD COLUMN tft_attention_heads INT NULL DEFAULT NULL COMMENT 'Number of attention heads in TFT'"),
                ("tft_dropout", "ALTER TABLE training_rounds ADD COLUMN tft_dropout FLOAT NULL DEFAULT NULL COMMENT 'Dropout rate for TFT (0.0-1.0)'"),
                ("tft_regularization_factor", "ALTER TABLE training_rounds ADD COLUMN tft_regularization_factor FLOAT NULL DEFAULT NULL COMMENT 'L2 regularization factor for TFT'"),
            ]
            
            for col_name, sql in round_columns:
                try:
                    connection.execute(text(sql))
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"  ℹ️  Column already exists: {col_name}")
                    else:
                        print(f"  ❌ Error adding {col_name}: {e}")
            
            connection.commit()
            print("\n✅ Phase 42 database update completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Database update failed: {e}")
            connection.rollback()
            return False

if __name__ == "__main__":
    success = add_columns()
    sys.exit(0 if success else 1)
