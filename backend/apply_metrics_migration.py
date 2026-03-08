"""
Direct migration to add missing metric columns to SQLite database
"""
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')

migrations = [
    # Add metrics to training_rounds table
    ('training_rounds', 'average_mape', 'FLOAT'),
    ('training_rounds', 'average_rmse', 'FLOAT'),
    ('training_rounds', 'average_r2', 'FLOAT'),
    ('training_rounds', 'average_accuracy', 'FLOAT'),
    # Add metrics to model_weights table
    ('model_weights', 'local_mape', 'FLOAT'),
    ('model_weights', 'local_rmse', 'FLOAT'),
    ('model_weights', 'local_r2', 'FLOAT'),
]

with engine.begin() as conn:
    for table, column, col_type in migrations:
        try:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            conn.execute(text(sql))
            print(f"✓ Added column {column} to {table}")
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print(f"⚠ Column {column} already exists in {table}")
            else:
                print(f"✗ Error adding {column} to {table}: {e}")

print("\n✓ Migration completed!")
