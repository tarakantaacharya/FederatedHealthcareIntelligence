"""Check model 5 details"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
import os

db = SessionLocal()
model = db.query(ModelWeights).filter(ModelWeights.id == 5).first()

if not model:
    print("❌ Model 5 not found")
else:
    print(f"✅ Model 5 found")
    print(f"   Hospital ID: {model.hospital_id}")
    print(f"   Model type: {model.model_type}")
    print(f"   Model architecture: {model.model_architecture}")
    print(f"   Training type: {model.training_type}")
    print(f"   Model path: {model.model_path}")
    print(f"   Path exists: {os.path.exists(model.model_path) if model.model_path else 'N/A'}")
    print(f"   Is uploaded: {model.is_uploaded}")
    print(f"   Round ID: {model.round_id}")
    print(f"   Dataset ID: {model.dataset_id}")
    
db.close()
