import sqlite3

conn = sqlite3.connect('federated_healthcare.db')
cursor = conn.cursor()

# Add columns to hospitals table
migrations = [
    ("ALTER TABLE hospitals ADD COLUMN verification_status VARCHAR(20) DEFAULT 'VERIFIED' NOT NULL", "hospitals.verification_status"),
    ("ALTER TABLE hospitals ADD COLUMN is_allowed_federated BOOLEAN DEFAULT TRUE NOT NULL", "hospitals.is_allowed_federated"),
    ("ALTER TABLE model_weights ADD COLUMN training_type VARCHAR(20) DEFAULT 'LOCAL' NOT NULL", "model_weights.training_type"),
    ("ALTER TABLE model_weights ADD COLUMN model_architecture VARCHAR(20) DEFAULT 'REGRESSION' NOT NULL", "model_weights.model_architecture"),
]

for sql, col_desc in migrations:
    try:
        cursor.execute(sql)
        print(f"✓ Added: {col_desc}")
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            print(f"⊙ Already exists: {col_desc}")
        else:
            print(f"✗ Error adding {col_desc}: {e}")

conn.commit()
conn.close()
print("\nSchema updates completed.")
