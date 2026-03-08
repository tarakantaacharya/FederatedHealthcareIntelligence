"""
Add model_type column to training_rounds table
Allows central admin to control which model architecture (TFT or ML_REGRESSION) is used per round
"""
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

settings = get_settings()
DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def migrate():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(training_rounds)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'model_type' in columns:
        print("✓ Column 'model_type' already exists in training_rounds table")
        conn.close()
        return
    
    try:
        print("Adding 'model_type' column to training_rounds table...")
        cursor.execute("""
            ALTER TABLE training_rounds 
            ADD COLUMN model_type VARCHAR(20) DEFAULT 'TFT' NOT NULL
        """)
        
        conn.commit()
        print("✓ Successfully added 'model_type' column with default 'TFT'")
        
        # Verify
        cursor.execute("PRAGMA table_info(training_rounds)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'model_type' in columns:
            print("✓ Migration verified successfully")
        else:
            print("✗ Migration verification failed")
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
    print("\n=== Migration Complete ===")
