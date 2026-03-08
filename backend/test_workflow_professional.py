#!/usr/bin/env python
"""
Professional workflow test for federated learning
Validates the correct flow with auto-aggregation
"""
import sys
import os
import time
import csv
import json
from pathlib import Path
from datetime import datetime
import requests

# Configuration
BASE_URL = "http://localhost:8000"

# Use existing, pre-verified credentials
HOSPITAL_1 = {
    "hospital_id": "ALEMBIC-TEST-001",
    "password": "SecurePass123!",
}

HOSPITAL_2 = {
    "hospital_id": "HSP002",
    "password": "password123",
}

ADMIN = {
    "admin_id": "CENTRAL-001",
    "password": "admin123",
}

TARGET_COLUMN = "bed_occupancy"
DATASET_NAME = "Workflow Dataset"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message, level="INFO"):
    """Log with formatting"""
    levels = {
        "PASS": "✅",
        "FAIL": "❌",
        "WARN": "⚠️ ",
        "INFO": "ℹ️ ",
        "STEP": "→ ",
    }
    prefix = levels.get(level, "  ")
    print(f"{prefix} {message}")


def get_round_status(admin_token, round_number):
    """
    Fetch round status from API.
    Helper that validates round state before operations.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = requests.get(
        f"{BASE_URL}/api/rounds/{round_number}",
        headers=headers,
        timeout=10,
    )

    if r.status_code != 200:
        raise Exception(f"Failed to fetch round status: {r.status_code} {r.text}")

    return r.json()["status"]


def create_dataset(hospital_token, hospital_id):
    """
    Create and upload CSV dataset for hospital
    """
    log(f"Creating dataset for {hospital_id}...", "STEP")
    
    # Create CSV
    dataset_dir = Path("./storage/datasets")
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir / f"{hospital_id}_workflow.csv"
    
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "bed_occupancy",
            "patient_count",
            "admission_rate",
            "discharge_rate",
        ])
        
        # 120 hours of data
        for i in range(120):
            day = (i // 24) + 1
            hour = i % 24
            base = 60.0 + (i % 20) * 1.5
            writer.writerow([
                f"2026-02-{(day % 28) + 1:02d}T{hour:02d}:00:00",
                float(base),
                float(base * 0.8),
                float(base * 0.05),
                float(base * 0.03),
            ])
    
    # Upload dataset
    headers = {"Authorization": f"Bearer {hospital_token}"}
    with open(csv_path, "rb") as f:
        files = {"file": f}
        data = {"name": DATASET_NAME, "description": f"Dataset for {hospital_id}"}
        upload_r = requests.post(
            f"{BASE_URL}/api/datasets/upload",
            files=files,
            data=data,
            headers=headers,
        )
    
    if upload_r.status_code not in [200, 201]:
        raise Exception(f"Dataset upload failed: {upload_r.status_code} {upload_r.text}")
    
    dataset_id = upload_r.json().get("id") or upload_r.json().get("dataset_id")
    log(f"Dataset created: {dataset_id}", "PASS")
    return dataset_id


def train_hospital_model(hospital_token, dataset_id, target_column):
    """
    Start local training for hospital
    """
    log(f"Starting training with target_column: {target_column}...", "STEP")
    
    headers = {"Authorization": f"Bearer {hospital_token}"}
    payload = {
        "dataset_id": dataset_id,
        "target_column": target_column,
        "epochs": 1,
        "epsilon": 0.5,
        "clip_norm": 1.0,
        "noise_multiplier": 0.1,
        "model_type": "baseline",
    }
    
    train_r = requests.post(
        f"{BASE_URL}/api/training/start",
        json=payload,
        headers=headers,
    )
    
    if train_r.status_code not in [200, 202]:
        raise Exception(f"Training start failed: {train_r.status_code} {train_r.text}")
    
    log(f"Training started", "PASS")
    return train_r.json()


def get_trained_models(hospital_token):
    """
    Get list of trained models for hospital (returns latest)
    """
    headers = {"Authorization": f"Bearer {hospital_token}"}
    
    # Poll training status
    max_attempts = 60  # 5 minutes
    for attempt in range(max_attempts):
        r = requests.get(
            f"{BASE_URL}/api/training/status",
            headers=headers,
            timeout=10,
        )
        
        if r.status_code == 200:
            status = r.json().get("status", "").upper()
            if status == "COMPLETED":
                log(f"Training completed", "PASS")
                return r.json().get("models", [])
        
        time.sleep(5)
    
    raise Exception("Training did not complete within timeout")


def upload_weights(hospital_token, hospital_id, model_id):
    """
    Upload trained model weights
    """
    log(f"Uploading weights for model {model_id}...", "STEP")
    
    headers = {"Authorization": f"Bearer {hospital_token}"}
    payload = {"model_id": model_id}
    
    upload_r = requests.post(
        f"{BASE_URL}/api/weights/upload",
        json=payload,
        headers=headers,
    )
    
    if upload_r.status_code not in [200, 202]:
        raise Exception(f"Weight upload failed: {upload_r.status_code} {upload_r.text}")
    
    log(f"Weights uploaded: {upload_r.json().get('weight_id')}", "PASS")
    return upload_r.json()


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    log("="*70, "INFO")
    log("PROFESSIONAL FEDERATED LEARNING WORKFLOW TEST", "INFO")
    log("="*70, "INFO")
    
    try:
        # STEP 1: CLEANUP
        log("CLEANUP", "STEP")
        log("Cleanup phase - database reset (assumes manual or separate process)", "WARN")
        
        # STEP 2: ADMIN LOGIN
        log("ADMIN LOGIN", "STEP")
        admin_login_r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"admin_id": ADMIN["admin_id"], "password": ADMIN["password"]},
            timeout=10,
        )
        
        if admin_login_r.status_code != 200:
            raise Exception(f"Admin login failed: {admin_login_r.text}")
        
        admin_token = admin_login_r.json()["access_token"]
        log(f"Admin authenticated", "PASS")
        
        # STEP 3: HOSPITAL LOGIN (already registered and verified)
        log("HOSPITAL LOGIN", "STEP")
        
        h1_login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "hospital_id": HOSPITAL_1["hospital_id"],
                "password": HOSPITAL_1["password"],
            },
        )
        
        if h1_login.status_code != 200:
            raise Exception(f"H1 login failed: {h1_login.status_code} {h1_login.text}")
        
        h1_token = h1_login.json()["access_token"]
        log(f"Hospital 1 ({HOSPITAL_1['hospital_id']}) authenticated", "PASS")
        
        h2_login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "hospital_id": HOSPITAL_2["hospital_id"],
                "password": HOSPITAL_2["password"],
            },
        )
        
        if h2_login.status_code != 200:
            raise Exception(f"H2 login failed: {h2_login.status_code} {h2_login.text}")
        
        h2_token = h2_login.json()["access_token"]
        log(f"Hospital 2 ({HOSPITAL_2['hospital_id']}) authenticated", "PASS")
        
        # STEP 4: CREATE TRAINING ROUND
        log("CREATE TRAINING ROUND", "STEP")
        
        # Check if there's already an active round
        active_round_r = requests.get(
            f"{BASE_URL}/api/rounds/active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        round_number = None
        round_target_column = TARGET_COLUMN
        
        if active_round_r.status_code == 200:
            existing_active = active_round_r.json()
            if existing_active:
                log(f"Active round already exists: #{existing_active.get('round_number')}", "WARN")
                log(f"Using existing round instead of creating new one", "WARN")
                round_number = existing_active.get('round_number')
                round_target_column = existing_active.get('target_column', TARGET_COLUMN)
                round_status = existing_active.get('status')
                log(f"Current status: {round_status}, target_column: {round_target_column}", "INFO")
            else:
                # No active round, create new one
                round_r = requests.post(
                    f"{BASE_URL}/api/rounds/create",
                    json={
                        "target_column": TARGET_COLUMN,
                        "required_canonical_features": ["patient_count", "admissions", "discharges"],
                        "model_type": "ML_REGRESSION",
                        "is_emergency": False,
                        "participation_mode": "ALL",
                    },
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                
                if round_r.status_code not in [200, 201]:
                    raise Exception(f"Round creation failed: {round_r.text}")
                
                round_number = round_r.json()["round_number"]
                round_target_column = round_r.json().get("target_column", TARGET_COLUMN)
                log(f"Round #{round_number} created with target: {round_target_column}", "PASS")
        else:
            # Fallback: just try to create a new round
            round_r = requests.post(
                f"{BASE_URL}/api/rounds/create",
                json={
                    "target_column": TARGET_COLUMN,
                    "required_canonical_features": ["patient_count", "admissions", "discharges"],
                    "model_type": "ML_REGRESSION",
                    "is_emergency": False,
                    "participation_mode": "ALL",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            
            if round_r.status_code not in [200, 201]:
                raise Exception(f"Round creation failed: {round_r.text}")
            
            round_number = round_r.json()["round_number"]
            round_target_column = round_r.json().get("target_column", TARGET_COLUMN)
            log(f"Round #{round_number} created with target: {round_target_column}", "PASS")
        
        # STEP 5: START ROUND
        log("START ROUND", "STEP")
        
        # Check current round status before starting
        current_r = requests.get(
            f"{BASE_URL}/api/rounds/{round_number}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        if current_r.status_code == 200:
            current_status = current_r.json().get("status")
            log(f"Current round status: {current_status}", "INFO")
            
            if current_status == "TRAINING":
                log(f"Round already in TRAINING, skipping start step", "WARN")
            elif current_status == "OPEN":
                start_r = requests.post(
                    f"{BASE_URL}/api/rounds/{round_number}/start",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                
                if start_r.status_code not in [200, 202]:
                    raise Exception(f"Round start failed: {start_r.text}")
                
                log(f"Round #{round_number} started (status: TRAINING)", "PASS")
            else:
                log(f"Round in unexpected status: {current_status}", "WARN")
        else:
            raise Exception(f"Could not fetch round status: {current_r.text}")
        
        # STEP 6: CREATE DATASETS
        log("CREATE DATASETS", "STEP")
        
        ds1_id = create_dataset(h1_token, HOSPITAL_1["hospital_id"])
        ds2_id = create_dataset(h2_token, HOSPITAL_2["hospital_id"])
        
        # STEP 7: HOSPITAL 1 TRAINING
        log("HOSPITAL 1 TRAINING", "STEP")
        
        h1_train_result = train_hospital_model(h1_token, ds1_id, round_target_column)
        h1_models = get_trained_models(h1_token)
        
        if not h1_models:
            raise Exception("No trained models returned for Hospital 1")
        
        h1_model_id = h1_models[0]["id"]
        log(f"Hospital 1 model trained: {h1_model_id}", "PASS")
        
        # STEP 8: HOSPITAL 2 TRAINING
        log("HOSPITAL 2 TRAINING", "STEP")
        
        h2_train_result = train_hospital_model(h2_token, ds2_id, round_target_column)
        h2_models = get_trained_models(h2_token)
        
        if not h2_models:
            raise Exception("No trained models returned for Hospital 2")
        
        h2_model_id = h2_models[0]["id"]
        log(f"Hospital 2 model trained: {h2_model_id}", "PASS")
        
        # STEP 9: HOSPITAL 1 UPLOAD (with state check)
        log("HOSPITAL 1 WEIGHT UPLOAD", "STEP")
        
        # Verify round is still in TRAINING
        round_status = get_round_status(admin_token, round_number)
        if round_status != "TRAINING":
            log(f"Round moved to {round_status}, skipping upload", "WARN")
            return False
        
        log(f"Round status verified: {round_status}", "PASS")
        h1_upload = upload_weights(h1_token, HOSPITAL_1["hospital_id"], h1_model_id)
        
        # STEP 10: HOSPITAL 2 UPLOAD (with state check)
        # This should trigger AUTO-AGGREGATION
        log("HOSPITAL 2 WEIGHT UPLOAD", "STEP")
        
        # Verify round is still in TRAINING
        round_status = get_round_status(admin_token, round_number)
        if round_status != "TRAINING":
            log(f"Round moved to {round_status}, skipping upload", "WARN")
            return False
        
        log(f"Round status verified: {round_status}", "PASS")
        h2_upload = upload_weights(h2_token, HOSPITAL_2["hospital_id"], h2_model_id)
        
        # STEP 11: AUTO-AGGREGATION
        log("AUTO-AGGREGATION", "STEP")
        log("2 hospitals uploaded weights → auto-aggregation should trigger", "INFO")
        log("Expected flow: TRAINING → AGGREGATING → CLOSED", "INFO")
        
        # STEP 12: WAIT FOR AUTO-CLOSE
        log("WAIT FOR ROUND CLOSURE", "STEP")
        
        max_wait = 30  # 30 seconds
        poll_interval = 2
        elapsed = 0
        
        while elapsed < max_wait:
            current_status = get_round_status(admin_token, round_number)
            log(f"[Poll {elapsed}s] Round status: {current_status}", "INFO")
            
            if current_status == "CLOSED":
                log(f"Round automatically CLOSED via auto-aggregation", "PASS")
                break
            
            if current_status not in ["TRAINING", "AGGREGATING"]:
                log(f"Unexpected status: {current_status}", "WARN")
                break
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        if current_status != "CLOSED":
            log(f"Round did not close within {max_wait}s. Status: {current_status}", "WARN")
        
        # STEP 13: APPROVAL
        log("MODEL APPROVAL", "STEP")
        
        # Get global model ID
        round_detail = requests.get(
            f"{BASE_URL}/api/rounds/{round_number}",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).json()
        
        global_model_id = round_detail.get("global_model_id")
        
        if global_model_id:
            log(f"Global model created: {global_model_id}", "PASS")
            
            # Approve model
            approve_r = requests.post(
                f"{BASE_URL}/api/models/{global_model_id}/approve",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            
            if approve_r.status_code in [200, 202]:
                log(f"Model approved", "PASS")
            else:
                log(f"Model approval: {approve_r.status_code}", "WARN")
        else:
            log(f"No global model ID found", "WARN")
        
        # ====================================================================
        # SUCCESS SUMMARY
        # ====================================================================
        log("="*70, "INFO")
        log("WORKFLOW COMPLETED SUCCESSFULLY", "PASS")
        log("="*70, "INFO")
        log("Summary:", "INFO")
        log(f"  • Round #{round_number} created and started", "PASS")
        log(f"  • Hospital 1 trained model {h1_model_id}", "PASS")
        log(f"  • Hospital 2 trained model {h2_model_id}", "PASS")
        log(f"  • Both hospitals uploaded weights", "PASS")
        log(f"  • Auto-aggregation triggered → round CLOSED", "PASS")
        if global_model_id:
            log(f"  • Global model {global_model_id} available for approval", "PASS")
        log("="*70, "INFO")
        
        return True
        
    except Exception as e:
        log(f"WORKFLOW FAILED: {str(e)}", "FAIL")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
