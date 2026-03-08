from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///D:/federated-healthcare/federated-healthcare/data/federated.db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT hospital_id, hospital_name, hashed_password FROM hospitals WHERE hospital_id = 'CGH-001'"))
    row = result.fetchone()
    if row:
        print(f'Hospital: {row[0]} - {row[1]}')
        print(f'Password hash: {row[2][:50]}...' if row[2] else 'NO PASSWORD SET!')
    else:
        print('Hospital CGH-001 not found')
