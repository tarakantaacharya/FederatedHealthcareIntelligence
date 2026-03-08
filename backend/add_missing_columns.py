import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='newpassword',
    database='federated_healthcare'
)
cursor = conn.cursor()

cursor.execute("SHOW COLUMNS FROM model_weights")
existing = set([row[0] for row in cursor.fetchall()])
print(f"Existing columns: {len(existing)}")

needed = ['local_mae', 'local_mse', 'local_adjusted_r2', 'local_smape', 'local_wape', 'local_mase', 'local_rmsle']
missing = [c for c in needed if c not in existing]

if missing:
    print(f"\nMissing columns to add: {missing}")
    for col in missing:
        try:
            cursor.execute(f"ALTER TABLE model_weights ADD COLUMN {col} FLOAT")
            print(f"  ✓ Added {col}")
        except Exception as e:
            print(f"  ✗ {col}: {e}")
    conn.commit()
    print("\n✓ All columns added to database")
else:
    print("\n✓ All required columns already exist")

conn.close()
