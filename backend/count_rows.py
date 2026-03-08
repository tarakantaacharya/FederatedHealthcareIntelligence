import sqlite3

conn = sqlite3.connect('federated.db')
cursor = conn.cursor()

tables = ['admins', 'hospitals', 'training_rounds', 'model_weights', 'blockchain']

print("\n" + "=" * 60)
print("DATABASE ROW COUNTS")
print("=" * 60)

for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:20} {count}")
    except Exception as e:
        print(f"{table:20} ERROR: {str(e)[:40]}")

conn.close()
