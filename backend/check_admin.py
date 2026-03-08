import sqlite3

conn = sqlite3.connect('federated.db')
cursor = conn.cursor()

# Check if admin table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
table_exists = cursor.fetchone()

if table_exists:
    print("✓ Admin table exists")
    cursor.execute("SELECT COUNT(*) FROM admin")
    count = cursor.fetchone()[0]
    print(f"  Row count: {count}")
    if count > 0:
        cursor.execute("SELECT admin_id, admin_name FROM admin LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - admin_id={row[0]}, admin_name={row[1]}")
else:
    print("✗ Admin table does NOT exist")

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nAll tables ({len(tables)}):")
for t in tables:
    print(f"  - {t[0]}")

conn.close()
