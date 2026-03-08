"""Direct MySQL column addition using pymysql"""
import pymysql
import sys

# Database connection details from config.py
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'newpassword',
    'database': 'federated_healthcare'
}

def add_missing_columns():
    """Add Phase 42 columns directly to MySQL"""
    try:
        print("Connecting to MySQL...")
        conn = pymysql.connect(**DB_CONFIG, autocommit=False)
        cursor = conn.cursor()
        
        # Add columns for model_weights table
        print("\n Adding columns to model_weights...")
        
        sqls_model_weights = [
            "ALTER TABLE model_weights ADD COLUMN actual_hyperparameters JSON NULL",
            "ALTER TABLE model_weights ADD COLUMN hyperparameter_compliant BOOLEAN NOT NULL DEFAULT FALSE"
        ]
        
        for sql in sqls_model_weights:
            try:
                cursor.execute(sql)
                conn.commit()
                col_name = sql.split('ADD COLUMN ')[1].split(' ')[0]
                print(f"  ✅ Added {col_name}")
            except pymysql.err.OperationalError as e:
                if '1060' in str(e):  # Duplicate column
                    col_name = sql.split('ADD COLUMN ')[1].split(' ')[0]
                    print(f"  ⚠️  {col_name} already exists")
                else:
                    print(f"  ❌ Error: {e}")
        
        # Add columns for training_rounds table
        print("\nAdding columns to training_rounds...")
        
        sqls_training_rounds = [
            "ALTER TABLE training_rounds ADD COLUMN tft_hidden_size INT NULL",
            "ALTER TABLE training_rounds ADD COLUMN tft_attention_heads INT NULL",
            "ALTER TABLE training_rounds ADD COLUMN tft_dropout FLOAT NULL",
            "ALTER TABLE training_rounds ADD COLUMN tft_regularization_factor FLOAT NULL"
        ]
        
        for sql in sqls_training_rounds:
            try:
                cursor.execute(sql)
                conn.commit()
                col_name = sql.split('ADD COLUMN ')[1].split(' ')[0]
                print(f"  ✅ Added {col_name}")
            except pymysql.err.OperationalError as e:
                if '1060' in str(e):  # Duplicate column
                    col_name = sql.split('ADD COLUMN ')[1].split(' ')[0]
                    print(f"  ⚠️  {col_name} already exists")
                else:
                    print(f"  ❌ Error: {e}")
        
        cursor.close()
        conn.close()
        print("\n✅ Database columns added successfully!")
        
    except Exception as e:
        print(f"\n❌ Failed to connect or execute: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_missing_columns()
