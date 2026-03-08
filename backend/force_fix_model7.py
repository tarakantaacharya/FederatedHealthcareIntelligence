"""Force update model 7's training schema with signature"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound
from sqlalchemy.orm.attributes import flag_modified
import json
import hashlib

db = SessionLocal()

# Get round 1
round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == 1).first()

# Calculate hyperparameter signature
hyperparameter_signature = hashlib.sha256(
    json.dumps(
        round_obj.required_hyperparameters,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode('utf-8')
).hexdigest()

# Get model 7
model = db.query(ModelWeights).filter(ModelWeights.id == 7).first()

print(f"Before update:")
print(f"  Has signature: {'federated_contract_signature' in (model.training_schema or {})}")

# Update training_schema
training_schema = model.training_schema or {}
training_schema['federated_contract_signature'] = {
    "feature_order_hash": round_obj.required_feature_order_hash,
    "model_architecture": round_obj.required_model_architecture,
    "hyperparameter_signature": hyperparameter_signature
}

# Force SQLAlchemy to detect the change
model.training_schema = training_schema
flag_modified(model, "training_schema")

db.commit()
db.refresh(model)

print(f"\nAfter update:")
print(f"  Has signature: {'federated_contract_signature' in (model.training_schema or {})}")
if 'federated_contract_signature' in (model.training_schema or {}):
    sig = model.training_schema['federated_contract_signature']
    print(f"  Feature order hash: {sig['feature_order_hash'][:16]}...")
    print(f"  Model architecture: {sig['model_architecture']}")
    print(f"  Hyperparameter signature: {sig['hyperparameter_signature'][:16]}...")
    print("\n✅ Signature successfully added!")
else:
    print("\n❌ Signature still missing")

db.close()
