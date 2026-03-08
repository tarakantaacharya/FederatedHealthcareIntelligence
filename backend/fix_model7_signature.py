"""Check round 1's contract requirements and add signature to model 7"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound
import json
import hashlib

db = SessionLocal()

# Get round 1
round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == 1).first()
if not round_obj:
    print("❌ Round 1 not found")
    db.close()
    exit(1)

print(f"=== Round 1 Contract ===")
print(f"  Feature order hash: {round_obj.required_feature_order_hash}")
print(f"  Model architecture: {round_obj.required_model_architecture}")
print(f"  Required hyperparameters: {json.dumps(round_obj.required_hyperparameters, indent=2)}")

# Calculate hyperparameter signature
if round_obj.required_hyperparameters:
    hyperparameter_signature = hashlib.sha256(
        json.dumps(
            round_obj.required_hyperparameters,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode('utf-8')
    ).hexdigest()
    print(f"  Hyperparameter signature: {hyperparameter_signature}")
else:
    hyperparameter_signature = None
    print("  No required hyperparameters")

# Get model 7
model = db.query(ModelWeights).filter(ModelWeights.id == 7).first()
if not model:
    print("\n❌ Model 7 not found")
    db.close()
    exit(1)

print(f"\n=== Fixing Model 7 ===")

# Add signature to training_schema
training_schema = model.training_schema or {}
training_schema['federated_contract_signature'] = {
    "feature_order_hash": round_obj.required_feature_order_hash,
    "model_architecture": round_obj.required_model_architecture,
    "hyperparameter_signature": hyperparameter_signature
}

model.training_schema = training_schema
db.commit()

print(f"✅ Added federated contract signature to model 7")
print(f"   Feature order hash: {round_obj.required_feature_order_hash}")
print(f"   Model architecture: {round_obj.required_model_architecture}")
print(f"   Hyperparameter signature: {hyperparameter_signature}")

db.close()
