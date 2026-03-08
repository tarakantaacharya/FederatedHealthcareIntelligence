"""Check all models in round 1 for missing signatures"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound  
from sqlalchemy.orm.attributes import flag_modified
import json
import hashlib

db = SessionLocal()

# Get round 1
round_obj = db.query(TrainingRound).filter(TrainingRound.id == 1).first()
if not round_obj:
    print("❌ Round 1 not found")
    db.close()
    exit(1)

print(f"=== Round 1 Models ===")
print(f"Round ID: {round_obj.id}, Round Number: {round_obj.round_number}")

# Get all federated models in round 1
models = db.query(ModelWeights).filter(
    ModelWeights.round_id == 1,
    ModelWeights.training_type == "FEDERATED",
    ModelWeights.is_uploaded == True
).all()

print(f"\nFound {len(models)} uploaded federated models")

# Calculate hyperparameter signature once
hyperparameter_signature = hashlib.sha256(
    json.dumps(
        round_obj.required_hyperparameters,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode('utf-8')
).hexdigest()

models_fixed = []
for model in models:
    has_signature = 'federated_contract_signature' in (model.training_schema or {})
    print(f"\nModel {model.id} (Hospital {model.hospital_id}):")
    print(f"  Has signature: {has_signature}")
    
    if not has_signature:
        print(f"  ⚠️  Adding signature...")
        training_schema = model.training_schema or {}
        training_schema['federated_contract_signature'] = {
            "feature_order_hash": round_obj.required_feature_order_hash,
            "model_architecture": round_obj.required_model_architecture,
            "hyperparameter_signature": hyperparameter_signature
        }
        model.training_schema = training_schema
        flag_modified(model, "training_schema")
        models_fixed.append(model.id)

if models_fixed:
    db.commit()
    print(f"\n✅ Fixed {len(models_fixed)} models: {models_fixed}")
else:
    print(f"\n✅ All models already have signatures")

db.close()
