"""Check model 7's training schema and signature"""
from app.database import SessionLocal
from app.models.model_weights import ModelWeights
import json

db = SessionLocal()
model = db.query(ModelWeights).filter(ModelWeights.id == 7).first()

if not model:
    print("❌ Model 7 not found")
else:
    print(f"✅ Model 7 found")
    print(f"   Hospital ID: {model.hospital_id}")
    print(f"   Training type: {model.training_type}")
    print(f"   Model architecture: {model.model_architecture}")
    print(f"   Round ID: {model.round_id}")
    print(f"   Round number: {model.round_number}")
    print(f"   Is uploaded: {model.is_uploaded}")
    print(f"\n=== Training Schema ===")
    if model.training_schema:
        print(json.dumps(model.training_schema, indent=2))
        
        if 'federated_contract_signature' in model.training_schema:
            print("\n✅ Federated contract signature EXISTS")
            sig = model.training_schema['federated_contract_signature']
            print(f"   Feature order hash: {sig.get('feature_order_hash', 'MISSING')}")
            print(f"   Model architecture: {sig.get('model_architecture', 'MISSING')}")
            print(f"   Hyperparameter signature: {sig.get('hyperparameter_signature', 'MISSING')}")
        else:
            print("\n❌ Federated contract signature MISSING")
    else:
        print("   (No training schema)")

db.close()
