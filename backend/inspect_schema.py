from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')
inspector = inspect(engine)

print('=== training_rounds columns ===')
for col in inspector.get_columns('training_rounds'):
    print(f'  {col["name"]}: {col["type"]}')

print('\n=== model_weights columns ===')
for col in inspector.get_columns('model_weights'):
    print(f'  {col["name"]}: {col["type"]}')
