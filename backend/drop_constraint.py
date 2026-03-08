"""Drop the problematic unique constraint that blocks multiple hospitals from training"""
import pymysql
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'newpassword',
    'database': 'federated_healthcare'
}

try:
    print("Connecting to MySQL...")
    conn = pymysql.connect(**DB_CONFIG, autocommit=False)
    cursor = conn.cursor()
    
    # Drop the problematic constraint
    print("\nDropping constraint 'uq_round_global_model'...")
    try:
        cursor.execute("ALTER TABLE model_weights DROP INDEX uq_round_global_model")
        conn.commit()
        print("  ✅ Constraint dropped successfully!")
    except pymysql.err.OperationalError as e:
        if '1091' in str(e):  # Can't DROP index - doesn't exist
            print("  ℹ️  Constraint doesn't exist (already dropped or never created)")
        else:
            print(f"  ❌ Error: {e}")
            sys.exit(1)
    
    # Verify remaining constraints
    print("\n=== Remaining constraints on model_weights ===")
    cursor.execute("""
        SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE 
        FROM information_schema.TABLE_CONSTRAINTS 
        WHERE TABLE_SCHEMA = 'federated_healthcare' 
        AND TABLE_NAME = 'model_weights'
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]})")
    
    cursor.close()
    conn.close()
    print("\n✅ Database constraint fix complete!")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    sys.exit(1)
