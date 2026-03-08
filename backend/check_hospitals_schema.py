from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')
inspector = inspect(engine)
print('=== hospitals table columns ===')
for col in inspector.get_columns('hospitals'):
    print(f'  {col["name"]}: {col["type"]}')
