import sqlite3

conn = sqlite3.connect('federated_healthcare.db')
cursor = conn.cursor()

# Check hospitals table columns
cursor.execute("PRAGMA table_info(hospitals)")
cols = cursor.fetchall()
col_names = [col[1] for col in cols]
print('hospitals columns:', col_names)
print('Has verification_status:', 'verification_status' in col_names)
print('Has is_allowed_federated:', 'is_allowed_federated' in col_names)
print()

# Check model_weights table columns
cursor.execute("PRAGMA table_info(model_weights)")
cols = cursor.fetchall()
col_names = [col[1] for col in cols]
print('model_weights columns:', col_names)
print('Has training_type:', 'training_type' in col_names)
print('Has model_architecture:', 'model_architecture' in col_names)

conn.close()
