import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/federated_healthcare")
engine = create_engine(db_url)

# Use raw SQL to avoid ORM initialization issues
with engine.connect() as conn:
    result = conn.execute(text(
        """SELECT id, hospital_id, round_number, training_type, model_architecture, is_global 
           FROM model_weights 
           ORDER BY created_at DESC 
           LIMIT 15"""
    ))
    
    models = result.fetchall()
    
    print(f"\n{'='*110}")
    print(f"Total models found: {len(models)}")
    print(f"{'='*110}\n")
    print(f"{'ID':>3} | {'Hospital':>8} | {'Round':>5} | {'TrainingType':>12} | {'Architecture':>14} | {'IsGlobal':>8}")
    print(f"{'-'*110}")
    for model in models:
        model_id, hospital_id, round_num, train_type, arch, is_global = model
        print(f"{model_id:3d} | {str(hospital_id):>8} | {round_num:>5d} | {str(train_type):>12} | {str(arch):>14} | {str(is_global):>8}")
    print(f"\n")


