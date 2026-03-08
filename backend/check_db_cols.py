"""Quick check for Phase 42 columns"""
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='newpassword', database='federated_healthcare')
cursor = conn.cursor()

print("\n=== model_weights columns ===")
cursor.execute("SHOW COLUMNS FROM model_weights WHERE Field IN ('actual_hyperparameters', 'hyperparameter_compliant')")
for row in cursor.fetchall():
    print(f"✅ {row[0]} - {row[1]}")

print("\n=== training_rounds columns ===")
cursor.execute("SHOW COLUMNS FROM training_rounds WHERE Field LIKE 'tft_%'")
for row in cursor.fetchall():
    print(f"✅ {row[0]} - {row[1]}")

cursor.close()
conn.close()
