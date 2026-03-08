#!/usr/bin/env python3
"""
Direct SQL migration to add metric columns to model_weights table
Bypasses Alembic to directly add columns to MySQL database
"""
import pymysql
import sys

def run_migration():
    """Execute migration directly against MySQL"""
    
    # Database connection details
    connection_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'newpassword',
        'database': 'federated_healthcare',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # SQL statements to add columns
    alter_statements = [
        "ALTER TABLE model_weights ADD COLUMN local_mae FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_mse FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_adjusted_r2 FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_smape FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_wape FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_mase FLOAT NULL;",
        "ALTER TABLE model_weights ADD COLUMN local_rmsle FLOAT NULL;",
    ]
    
    try:
        connection = pymysql.connect(**connection_config)
        cursor = connection.cursor()
        
        print("Connecting to MySQL database...")
        print(f"Host: {connection_config['host']}")
        print(f"Database: {connection_config['database']}")
        print()
        
        for stmt in alter_statements:
            try:
                print(f"Executing: {stmt}")
                cursor.execute(stmt)
                print("  ✓ Success")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e):
                    print(f"  ⓘ Column already exists (skipping)")
                else:
                    print(f"  ✗ Error: {e}")
                    raise
        
        connection.commit()
        
        # Verify columns exist
        print("\nVerifying columns...")
        cursor.execute("SHOW COLUMNS FROM model_weights;")
        columns = cursor.fetchall()
        col_names = [col['Field'] for col in columns]
        
        required_cols = ['local_mae', 'local_mse', 'local_adjusted_r2', 'local_smape', 'local_wape', 'local_mase', 'local_rmsle']
        
        for col in required_cols:
            if col in col_names:
                print(f"  ✓ {col} exists")
            else:
                print(f"  ✗ {col} missing")
                return False
        
        print("\n✓ Migration completed successfully")
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"Database connection error: {e}")
        print("\nMake sure:")
        print("  1. MySQL is running")
        print("  2. Database: federated_healthcare exists")
        print("  3. User: root with password 'newpassword' can connect")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
