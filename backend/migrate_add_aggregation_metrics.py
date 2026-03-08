"""
Migration: Add aggregation metrics columns to training_rounds table
Adds: average_mape, average_rmse, average_r2, average_accuracy
"""
import sqlite3
from app.config import get_settings
import os
from pathlib import Path

settings = get_settings()

def migrate_sqlite():
    """Migrate SQLite database"""
    # Parse SQLite path from DATABASE_URL
    db_url = settings.DATABASE_URL
    if 'sqlite:///' in db_url:
        db_path = db_url.replace('sqlite:///', '')
    else:
        db_path = "data/federated.db"
    
    # Convert to absolute path if relative
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"✗ SQLite database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add columns if they don't exist
        columns_to_add = {
            'average_mape': 'REAL',
            'average_rmse': 'REAL',
            'average_r2': 'REAL',
            'average_accuracy': 'REAL'
        }
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(training_rounds)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE training_rounds ADD COLUMN {col_name} {col_type}")
                print(f"✓ Added column: {col_name}")
            else:
                print(f"✓ Column already exists: {col_name}")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(training_rounds)")
        columns = cursor.fetchall()
        print(f"\n✓ Final training_rounds columns ({len(columns)} total):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"✗ SQLite migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run migration"""
    db_url = settings.DATABASE_URL
    
    if not db_url:
        print("✗ DATABASE_URL not set")
        return False
    
    if 'sqlite' in db_url:
        print("🔄 Migrating SQLite database...")
        return migrate_sqlite()
    else:
        print(f"✗ Unsupported database: {db_url}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Training Rounds Aggregation Metrics Migration")
    print("=" * 60)
    
    success = main()
    
    print("=" * 60)
    if success:
        print("✓ Migration completed successfully!")
    else:
        print("✗ Migration failed!")
    print("=" * 60)
