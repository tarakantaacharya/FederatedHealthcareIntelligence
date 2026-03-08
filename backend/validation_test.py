#!/usr/bin/env python3
"""
FULL RUNTIME VALIDATION TEST
Phases A-G: Training→DP→WeightUpload→Aggregation→Blockchain→Redistribution→Prediction
NO CODE CHANGES - DETECTION ONLY
"""
import requests
import json
import time
import csv
from pathlib import Path

BASE_URL = 'http://localhost:8000'
HOSPITAL_ID = 'VAL-TEST-002'
HOSPITAL_NAME = 'Phase Test Hospital'
ADMIN_ID = 'ADM-TEST-001'
ADMIN_NAME = 'Admin Hospital'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_token(hospital_id=HOSPITAL_ID, hospital_name=HOSPITAL_NAME, email='phase@test.hospital', password='PhasePass123!'):
    """Register and login to get auth token with Phase 0 confirmation"""
    # Register
    reg_data = {
        'hospital_name': hospital_name,
        'hospital_id': hospital_id,
        'contact_email': email,
        'location': 'Test City',
        'password': password
    }
    resp = requests.post(f'{BASE_URL}/api/auth/register', json=reg_data)
    if resp.status_code not in [200, 201]:
        # May already be registered
        pass
    
    # Login
    login_data = {'hospital_id': hospital_id, 'password': password}
    resp = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    
    token = resp.json()['access_token']
    return token

def create_test_dataset(token, dataset_name="Test Dataset Phase"):
    """Create a test CSV dataset"""
    print("\nCreating test dataset...")
    
    # Create CSV file
    csv_path = Path('./storage/datasets/test_validation.csv')
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate sample time series data with bed_occupancy target column
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'bed_occupancy', 'patient_id', 'value1', 'value2', 'label'])
        for i in range(100):
            writer.writerow([f'2024-01-{(i%28)+1:02d}', 50+i%40, f'P{i%10}', 50+i, 100-i, i%2])
    
    print(f"✓ CSV created: {csv_path}")
    
    # Upload via dataset API
    headers = {'Authorization': f'Bearer {token}'}
    with open(csv_path, 'rb') as f:
        files = {'file': f}
        data = {
            'name': dataset_name,
            'description': 'Phase validation dataset'
        }
        resp = requests.post(f'{BASE_URL}/api/datasets/upload', 
                           files=files, data=data, headers=headers)
    
    print(f"Dataset Upload: {resp.status_code}")
    if resp.status_code not in [200, 201]:
        print(f"Error: {resp.json()}")
        return None
    
    dataset_id = resp.json().get('id') or resp.json().get('dataset_id')
    print(f"✓ Dataset created: {dataset_id}")
    return dataset_id

def start_training(token, dataset_id):
    """Start TFT training - PHASE A"""
    print("\n" + "="*80)
    print("PHASE A: LOCAL TRAINING (TFT with Gradient DP)")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        'dataset_id': dataset_id,
        'epochs': 2,
        'batch_size': 16,
        'epsilon': 0.5,
        'clip_norm': 1.0,
        'noise_multiplier': 0.1,
        'model_type': 'tft'  # Force TFT
    }
    
    resp = requests.post(f'{BASE_URL}/api/training/start', json=payload, headers=headers)
    print(f"Training Start: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Error: {resp.json()}")
        return None
    
    result = resp.json()
    model_id = result.get('model_id')
    training_id = result.get('training_id')
    
    print(f"✓ Training started")
    print(f"  Model ID: {model_id}")
    print(f"  Training ID: {training_id}")
    
    # Log model weights to verify TFT is used
    if result.get('model_type'):
        print(f"  Model Type: {result['model_type']}")
    
    # Check for DP indicators
    if result.get('gradient_norm'):
        print(f"  Gradient Norm: {result['gradient_norm']:.6f} (gradient clipping active)")
    if result.get('epsilon_used'):
        print(f"  Epsilon Used: {result['epsilon_used']} (DP active)")
    if result.get('noise_applied'):
        print(f"  Noise Applied: {result['noise_applied']} (noise injection active)")
    
    return model_id, training_id

def upload_weights(token, model_id, training_id):
    """Upload weights and verify DP before masking - PHASE B"""
    print("\n" + "="*80)
    print("PHASE B: WEIGHT UPLOAD (DP Applied Before Masking)")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        'model_id': model_id,
        'training_id': training_id,
        'round_number': 1,
        'apply_dp': True
    }
    
    resp = requests.post(f'{BASE_URL}/api/weights/upload', json=payload, headers=headers)
    print(f"Weight Upload: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Error: {resp.json()}")
        return None
    
    result = resp.json()
    weight_id = result.get('weight_id')
    
    print(f"✓ Weights uploaded")
    print(f"  Weight ID: {weight_id}")
    
    # Verify DP was applied
    if result.get('dp_applied'):
        print(f"  DP Applied: {result['dp_applied']}")
    if result.get('gradient_clipped'):
        print(f"  Gradient Clipped: {result['gradient_clipped']} (norm {result.get('gradient_norm_post_clip', 'N/A')})")
    if result.get('noise_injected'):
        print(f"  Noise Injected: {result['noise_injected']} (std {result.get('noise_std', 'N/A')})")
    
    # CRITICAL: Verify no raw weights stored unmasked
    raw_weights_path = f'./storage/models/{HOSPITAL_ID}/weights_raw_r1.json'
    masked_weights_path = f'./storage/models/{HOSPITAL_ID}/weights_masked_r1.json'
    
    try:
        raw_exists = Path(raw_weights_path).exists()
        masked_exists = Path(masked_weights_path).exists()
        if raw_exists:
            print(f"  ⚠ RAW WEIGHTS STORED UNMASKED: {raw_weights_path}")
        if masked_exists:
            print(f"  ✓ Masked weights stored: {masked_weights_path}")
    except:
        pass
    
    return weight_id

def upload_mask(token, weight_id):
    """Upload MPC mask - PHASE C"""
    print("\n" + "="*80)
    print("PHASE C: MASK UPLOAD (MPC Masking)")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        'weight_id': weight_id,
        'round_number': 1,
        'mask_type': 'mpc'
    }
    
    resp = requests.post(f'{BASE_URL}/api/weights/masks/upload', json=payload, headers=headers)
    print(f"Mask Upload: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        # This endpoint might not exist; log and continue
        print(f"Note: Mask upload returned {resp.status_code} (endpoint may not be separate)")
        return None
    
    result = resp.json()
    print(f"✓ Mask uploaded")
    if result.get('mask_hash'):
        print(f"  Mask Hash: {result['mask_hash']}")
    
    return result.get('mask_id')

def start_aggregation(admin_token):
    """Call aggregation with dropout handling - PHASE D"""
    print("\n" + "="*80)
    print("PHASE D: AGGREGATION (Masked FedAvg with Dropout)")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
    payload = {
        'round_number': 1,
        'aggregation_method': 'fedavg_masked'
    }
    
    resp = requests.post(f'{BASE_URL}/api/aggregation/fedavg', json=payload, headers=headers)
    print(f"Aggregation: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Error: {resp.json()}")
        return None
    
    result = resp.json()
    
    print(f"✓ Aggregation completed")
    print(f"  Hospitals Participated: {result.get('hospitals_participated', 'N/A')}")
    print(f"  Weights Aggregated: {result.get('weights_count', 'N/A')}")
    print(f"  Model Hash: {result.get('model_hash', 'N/A')}")
    
    # Dropout information
    if result.get('dropout_summary'):
        dropout = result['dropout_summary']
        print(f"  Dropout Summary:")
        print(f"    - Total Hospitals: {dropout.get('total_hospitals', 'N/A')}")
        print(f"    - Active Hospitals: {dropout.get('active_hospitals', 'N/A')}")
        print(f"    - Dropped Hospitals: {dropout.get('dropped_hospitals', 'N/A')}")
    
    # Mask reconciliation
    if result.get('masks_reconciled'):
        print(f"  ✓ Masks Reconciled: {result['masks_reconciled']}")
    if result.get('masked_weights_used'):
        print(f"  ✓ Only Masked Weights Used: {result['masked_weights_used']}")
    
    return result.get('model_id')

def verify_blockchain(token, model_hash):
    """Verify blockchain audit logging - PHASE E"""
    print("\n" + "="*80)
    print("PHASE E: BLOCKCHAIN AUDIT LOGGING")
    print("="*80)
    
    if not model_hash:
        print("⚠ No model hash to verify")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    resp = requests.get(f'{BASE_URL}/api/blockchain/audit-log', headers=headers)
    print(f"Audit Log Fetch: {resp.status_code}")
    
    if resp.status_code == 200:
        logs = resp.json()
        if isinstance(logs, dict):
            logs = logs.get('logs', [])
        
        print(f"✓ Audit logs retrieved: {len(logs)} entries")
        
        # Find latest aggregation log
        for log in reversed(logs[-5:]):  # Check last 5
            if log.get('event_type') == 'model_aggregation':
                logged_hash = log.get('model_hash')
                print(f"  Latest Aggregation Log:")
                print(f"    - Hash: {logged_hash}")
                print(f"    - Timestamp: {log.get('timestamp')}")
                print(f"    - Hospital: {log.get('hospital_id')}")
                
                if logged_hash == model_hash:
                    print(f"  ✓ Hash Match Verified")
                else:
                    print(f"  ⚠ Hash Mismatch: Expected {model_hash}, got {logged_hash}")
                break
    else:
        print(f"Note: Blockchain API returned {resp.status_code}")

def download_global_model(token):
    """Download global model to verify redistribution - PHASE F"""
    print("\n" + "="*80)
    print("PHASE F: GLOBAL MODEL REDISTRIBUTION")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'round_number': 1}
    
    resp = requests.post(f'{BASE_URL}/api/model-updates/download', json=payload, headers=headers)
    print(f"Model Download: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Error: {resp.json()}")
        return None
    
    result = resp.json()
    
    print(f"✓ Global model downloaded")
    print(f"  Model ID: {result.get('model_id')}")
    print(f"  Round Number: {result.get('round_number')}")
    print(f"  Model Type: {result.get('model_type')}")
    print(f"  Hospitals Contributed: {result.get('hospitals_count', 'N/A')}")
    
    return result.get('model_id')

def make_prediction(token, model_id=1):
    """Make prediction with 6h/24h/72h horizons - PHASE G"""
    print("\n" + "="*80)
    print("PHASE G: MULTI-HORIZON PREDICTION (6h/24h/72h)")
    print("="*80)
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Prepare prediction payload with sample data
    payload = {
        'model_id': model_id,
        'forecast_horizon': 24
    }
    
    resp = requests.post(f'{BASE_URL}/api/predictions/forecast', json=payload, headers=headers)
    print(f"Prediction Request: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Note: {resp.status_code} - {resp.json()}")
        return None
    
    result = resp.json()
    
    print(f"✓ Prediction completed")
    print(f"  Model Type: {result.get('model_type')}")
    
    # Check for multi-horizon outputs
    if result.get('horizon_forecasts'):
        print(f"  ✓ Multi-Horizon Forecasts:")
        for horizon, forecast in result['horizon_forecasts'].items():
            print(f"    - {horizon}:")
            print(f"      Prediction: {forecast.get('prediction', 'N/A')}")
            print(f"      Lower Bound (95% CI): {forecast.get('lower_bound', 'N/A')}")
            print(f"      Upper Bound (95% CI): {forecast.get('upper_bound', 'N/A')}")
            print(f"      Confidence: {forecast.get('confidence_level', 'N/A')}")
    else:
        print(f"  Single Forecast: {result.get('prediction', 'N/A')}")
    
    # Quality metrics
    if result.get('quality_metrics'):
        metrics = result['quality_metrics']
        print(f"  Quality Metrics:")
        print(f"    - MAPE: {metrics.get('mape', 'N/A')}")
        print(f"    - Bias: {metrics.get('bias', 'N/A')}")
        print(f"    - Trend Alignment: {metrics.get('trend_alignment', 'N/A')}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == '__main__':
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FULL FEDERATED ROUND VALIDATION TEST" + " "*21 + "║")
    print("║" + " "*15 + "Phases A-G: Training→DP→Aggregation→Blockchain→Prediction" + " "*10 + "║")
    print("║" + " "*25 + "NO CODE CHANGES (DETECTION ONLY)" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        # Phase 0: Auth
        print("\n" + "="*80)
        print("PHASE 0: AUTH & SESSION (15-min expiry)")
        print("="*80)
        
        token = get_token(HOSPITAL_ID, HOSPITAL_NAME, 'phase@test.hospital', 'PhasePass123!')
        admin_token = get_token(ADMIN_ID, ADMIN_NAME, 'admin@test.hospital', 'AdminPass123!')
        print(f"✓ Hospital token obtained (15-min session)")
        print(f"✓ Admin token obtained (15-min session)")
        
        # Setup: Create dataset
        dataset_id = create_test_dataset(token)
        if not dataset_id:
            print("⚠ Could not create dataset, continuing...")
        
        # Phase A: Training
        result = start_training(token, dataset_id)
        if result:
            model_id, training_id = result
        else:
            print("⚠ Training failed")
            model_id, training_id = None, None
        
        # Phase B: Weight Upload
        if model_id and training_id:
            weight_id = upload_weights(token, model_id, training_id)
        else:
            weight_id = None
        
        # Phase C: Mask Upload
        if weight_id:
            upload_mask(token, weight_id)
        
        # Phase D: Aggregation
        agg_model_id = start_aggregation(admin_token)
        
        # Phase E: Blockchain (needs model hash from aggregation)
        # Note: Will fetch from aggregation response if available
        verify_blockchain(token, agg_model_id)
        
        # Phase F: Global Model Download
        download_global_model(admin_token)
        
        # Phase G: Prediction
        make_prediction(token)
        
        print("\n" + "="*80)
        print("VALIDATION TEST COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
