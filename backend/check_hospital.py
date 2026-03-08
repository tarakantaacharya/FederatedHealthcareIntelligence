from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

# Get hospital info
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, hospital_id, hospital_name FROM hospitals WHERE hospital_id = "TEST-001" LIMIT 1'))
    rows = result.fetchall()
    if rows:
        print(f"Hospital found: ID={rows[0][0]} hospital_id={rows[0][1]} name={rows[0][2]}")
    else:
        print("Hospital TEST-001 not found")
        # List all hospitals
        result = conn.execute(text('SELECT id, hospital_id, hospital_name FROM hospitals LIMIT 5'))
        print("Available hospitals:")
        for row in result.fetchall():
            print(f"  ID={row[0]} hospital_id={row[1]} name={row[2]}")
