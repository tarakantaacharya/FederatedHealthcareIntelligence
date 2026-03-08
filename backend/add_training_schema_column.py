"""
Database migration script to add training_schema JSON column to model_weights table.

This script adds the new training_schema column that stores schema metadata for
models, enabling automatic feature alignment during inference.

Supports both SQLite and MySQL databases.

Usage:
    python add_training_schema_column.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.config import get_settings

def migrate():
    """Add training_schema column to model_weights table"""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    print("[MIGRATION] Starting migration: Add training_schema column")
    print(f"[MIGRATION] Database: {engine.dialect.name}")
    
    with engine.connect() as conn:
        # Check if column already exists using SQLAlchemy inspector (works for all databases)
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('model_weights')]
        
        if 'training_schema' in columns:
            print("[MIGRATION] Column 'training_schema' already exists - skipping")
            return
        
        # Add the column (syntax varies by database)
        print("[MIGRATION] Adding training_schema column...")
        
        if engine.dialect.name == 'sqlite':
            # SQLite: No JSON type, use TEXT; no COMMENT support
            conn.execute(text("""
                ALTER TABLE model_weights 
                ADD COLUMN training_schema TEXT
            """))
            conn.commit()
        elif engine.dialect.name == 'mysql':
            # MySQL: JSON type with COMMENT
            conn.execute(text("""
                ALTER TABLE model_weights 
                ADD COLUMN training_schema JSON NULL
                COMMENT 'Schema metadata from training (required_columns, excluded_columns, target_column, num_features)'
            """))
            conn.commit()
        else:
            # PostgreSQL and others: JSON or JSONB type
            conn.execute(text("""
                ALTER TABLE model_weights 
                ADD COLUMN training_schema JSON
            """))
            conn.commit()
        
        print("[MIGRATION] ✅ Successfully added training_schema column")
        print("[MIGRATION] Note: Existing models will have NULL training_schema")
        print("[MIGRATION] New models will automatically save schema metadata during training")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"[MIGRATION] ❌ Migration failed: {e}")
        sys.exit(1)
