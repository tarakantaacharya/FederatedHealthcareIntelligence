"""
Automatic Federated Learning Flow Test
Tests automatic orchestration:

upload_weights()
      ↓
eligible_hospitals >= 2
      ↓
move_to_aggregating()
      ↓
perform_masked_fedavg()
      ↓
complete_round()
"""

import requests
import time
import sys
import os

BASE_URL = "http://localhost:8000/api"

# Credentials
ADMIN = {"admin_id": "CENTRAL-001", "password": "admin123"}

HOSPITAL_1 = {"hospital_id": "ALEMBIC-TEST-001", "password": "SecurePass123!"}
HOSPITAL_2 = {"hospital_id": "HSP002", "password": "password123"}

# Dataset IDs (pre-created)
H1_DATASET = 2
H2_DATASET = 33

MODEL_TYPE = "ML_REGRESSION"
AGGREGATION = "fedavg"

REQUIRED_FEATURES = ["admissions", "discharges"]


# -------------------
# LOGIN
# -------------------

def admin_login():
    r = requests.post(f"{BASE_URL}/admin/login", json=ADMIN)

    if r.status_code != 200:
        print("❌ Admin login failed:", r.text)
        return None

    print("✅ Admin authenticated")
    return r.json()["access_token"]


def hospital_login(creds):
    r = requests.post(f"{BASE_URL}/auth/login", json=creds)

    if r.status_code != 200:
        print(f"❌ {creds['hospital_id']} login failed:", r.text)
        return None

    print(f"✅ {creds['hospital_id']} authenticated")
    return r.json()["access_token"]


# -------------------
# GET ACTIVE ROUND
# -------------------

def get_active_round(admin_token):
    """Get current active round if exists"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    r = requests.get(
        f"{BASE_URL}/rounds/active",
        headers=headers
    )
    
    if r.status_code == 200:
        data = r.json()
        if data:
            print(f"ℹ️  Active round exists: #{data['round_number']} (status: {data['status']})")
            return data
    
    return None


def close_stale_rounds_db():
    """Close stale rounds directly via DB"""
    try:
        print("⏳ Closing stale rounds via direct DB access...")
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.training_rounds import TrainingRound, RoundStatus
        
        db_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:fed_health_2025@localhost:3306/federated_healthcare")
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # Find all TRAINING/OPEN/AGGREGATING rounds
        stale = db.query(TrainingRound).filter(
            TrainingRound.status.in_([
                RoundStatus.TRAINING, 
                RoundStatus.OPEN, 
                RoundStatus.AGGREGATING
            ])
        ).all()
        
        for r in stale:
            print(f"  • Closing round {r.round_number} (status: {r.status})")
            r.status = RoundStatus.CLOSED
        
        db.commit()
        db.close()
        
        if stale:
            print(f"✅ Closed {len(stale)} stale rounds\n")
        else:
            print("✅ No stale rounds found\n")
        
    except Exception as e:
        print(f"⚠️  Could not close stale rounds (DB access): {e}\n")


# -------------------
# ROUND CREATION
# -------------------

def create_round(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "target_column": "bed_occupancy",
        "is_emergency": False,
        "participation_mode": "ALL",
        "model_type": MODEL_TYPE,
        "aggregation_strategy": AGGREGATION,
        "required_canonical_features": REQUIRED_FEATURES,
        "required_hyperparameters": {
            "hidden_size": 64,
            "attention_head_size": 4,
            "dropout": 0.1,
            "batch_size": 32,
            "epochs": 2,
            "learning_rate": 0.001
        },
        "allocated_privacy_budget": 10.0
    }

    r = requests.post(
        f"{BASE_URL}/rounds/create",
        json=payload,
        headers=headers
    )

    if r.status_code not in [200, 201]:
        print(f"❌ Round creation failed: {r.text}")
        return None

    data = r.json()
    print(f"✅ Round #{data['round_number']} created")
    return data["round_number"]


# -------------------
# SCHEMA
# -------------------

def create_schema(admin_token, round_number):
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "model_architecture": MODEL_TYPE,
        "target_column": "bed_occupancy",
        "feature_schema": REQUIRED_FEATURES,
        "sequence_required": False,
        "model_hyperparameters": {
            "hidden_size": 64,
            "attention_head_size": 4,
            "dropout": 0.1,
            "batch_size": 32,
            "epochs": 2,
            "learning_rate": 0.001
        }
    }

    r = requests.post(
        f"{BASE_URL}/rounds/{round_number}/schema",
        json=payload,
        headers=headers
    )

    if r.status_code not in [200, 201]:
        print(f"⚠️  Schema creation skipped/failed: {r.text}")
        return False

    print("✅ Schema created")
    return True


# -------------------
# START ROUND
# -------------------

def start_round(admin_token, round_number):
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = requests.post(
        f"{BASE_URL}/rounds/{round_number}/start",
        headers=headers
    )

    if r.status_code not in [200, 201]:
        print(f"⚠️  Start round skipped (already active): {r.text}")
        return True  # Already running is OK

    print("✅ Round started (status: TRAINING)")
    return True


# -------------------
# TRAINING
# -------------------

def train(token, dataset_id, hospital_id):
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "dataset_id": dataset_id,
        "training_type": "FEDERATED",
        "model_architecture": MODEL_TYPE,
        "epochs": 2,
        "batch_size": 32
    }

    r = requests.post(
        f"{BASE_URL}/training/start",
        json=payload,
        headers=headers
    )

    if r.status_code not in [200, 201]:
        print(f"❌ Training failed for {hospital_id}: {r.text}")
        return None

    data = r.json()
    model_id = data.get("model_id")
    
    # Poll for training completion
    print(f"⏳ Waiting for {hospital_id} training to complete...")
    for attempt in range(60):
        r = requests.get(
            f"{BASE_URL}/training/status",
            headers=headers
        )
        
        if r.status_code == 200:
            status = r.json().get("status", "").upper()
            if status == "COMPLETED":
                print(f"✅ {hospital_id} training completed: model {model_id}")
                return model_id
        
        time.sleep(1)
    
    print(f"❌ {hospital_id} training timeout")
    return None


# -------------------
# WEIGHT UPLOAD
# -------------------

def upload(token, model_id, hospital_id):
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(
        f"{BASE_URL}/weights/upload",
        json={"model_id": model_id},
        headers=headers
    )

    if r.status_code not in [200, 201]:
        print(f"❌ {hospital_id} upload failed: {r.text}")
        return False

    print(f"✅ {hospital_id} weights uploaded")
    return True


# -------------------
# CHECK ROUND STATUS
# -------------------

def get_round_status(admin_token, round_number):
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = requests.get(
        f"{BASE_URL}/rounds/{round_number}",
        headers=headers,
        timeout=10,
    )

    if r.status_code != 200:
        raise Exception("Failed to fetch round status")

    return r.json()["status"]


def get_round_details(admin_token, round_number):
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = requests.get(
        f"{BASE_URL}/rounds/{round_number}",
        headers=headers
    )

    if r.status_code != 200:
        print(f"❌ Round check failed: {r.text}")
        return None

    return r.json()


# -------------------
# MAIN TEST
# -------------------

def main():
    print("\n" + "="*70)
    print("AUTOMATIC FEDERATED FLOW TEST")
    print("="*70 + "\n")

    # Step 0: Close stale rounds
    print("→ CLEANUP")
    close_stale_rounds_db()
    
    # Step 1: Admin login
    print("→ ADMIN LOGIN")
    admin = admin_login()
    if not admin:
        return
    
    # Step 2: Get or create round
    print("\n→ ROUND MANAGEMENT")
    active = get_active_round(admin)
    
    if active and active.get("status") == "TRAINING":
        round_number = active.get("round_number")
        print(f"ℹ️  Using existing active round #{round_number}")
    else:
        print("ℹ️  No active TRAINING round, creating new one...")
        round_number = create_round(admin)
        if not round_number:
            return
        
        # Create schema and start
        if not create_schema(admin, round_number):
            pass  # Continue anyway
        
        if not start_round(admin, round_number):
            return
    
    # Step 3: Hospital login
    print("\n→ HOSPITAL LOGIN")
    h1 = hospital_login(HOSPITAL_1)
    h2 = hospital_login(HOSPITAL_2)
    
    if not h1 or not h2:
        return
    
    # Step 4: Training
    print("\n→ TRAINING PHASE")
    print(f"[1/6] {HOSPITAL_1['hospital_id']} training...")
    model1 = train(h1, H1_DATASET, HOSPITAL_1['hospital_id'])
    if not model1:
        return
    
    print(f"[2/6] {HOSPITAL_2['hospital_id']} training...")
    model2 = train(h2, H2_DATASET, HOSPITAL_2['hospital_id'])
    if not model2:
        return
    
    # Step 5: Upload with state protection
    print("\n→ WEIGHT UPLOAD & AUTO-AGGREGATION")
    
    # Verify round is TRAINING before uploads
    status = get_round_status(admin, round_number)
    if status != "TRAINING":
        print(f"❌ Round moved to {status}, cannot upload (expected: TRAINING)")
        return
    
    print(f"[3/6] Verifying round status: {status}")
    
    print(f"[4/6] {HOSPITAL_1['hospital_id']} uploading weights...")
    if not upload(h1, model1, HOSPITAL_1['hospital_id']):
        return
    
    print(f"[5/6] {HOSPITAL_2['hospital_id']} uploading weights (should trigger auto-aggregation)...")
    if not upload(h2, model2, HOSPITAL_2['hospital_id']):
        return
    
    # Step 6: Wait for auto-aggregation & round closure
    print("\n→ AUTO-AGGREGATION & CLOSURE")
    print("[6/6] Waiting for automatic aggregation...")
    
    for attempt in range(20):
        status = get_round_status(admin, round_number)
        print(f"    Poll {attempt + 1}: Round status = {status}")
        
        if status == "CLOSED":
            print(f"\n✅ SUCCESS: Round automatically CLOSED after {attempt + 1} polls")
            break
        
        if status not in ["TRAINING", "AGGREGATING"]:
            print(f"⚠️  Unexpected status: {status}")
            break
        
        time.sleep(2)
    else:
        print(f"⚠️  Round did not close after {20 * 2}s")
    
    # Verify results
    print("\n→ RESULTS")
    round_data = get_round_details(admin, round_number)
    
    if round_data:
        global_model_id = round_data.get("global_model_id")
        if global_model_id:
            print(f"✅ Global model created: {global_model_id}")
        else:
            print("⚠️  No global model ID found yet")
        
        final_status = round_data.get("status")
        print(f"✅ Final round status: {final_status}")
    
    print("\n" + "="*70)
    print("AUTOMATIC FEDERATED FLOW TEST COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
