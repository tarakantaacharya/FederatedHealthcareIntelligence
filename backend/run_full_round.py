#!/usr/bin/env python3
"""Run full federated round with 2 hospitals and admin."""
import csv
import json
import time
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"

suffix = str(int(time.time()))[-6:]

hospitals = [
    {
        "name": f"Hospital Alpha {suffix}",
        "id": f"HOSP-A-{suffix}",
        "email": f"alpha{suffix}@test.hospital",
        "password": "AlphaPass123!",
    },
    {
        "name": f"Hospital Beta {suffix}",
        "id": f"HOSP-B-{suffix}",
        "email": f"beta{suffix}@test.hospital",
        "password": "BetaPass123!",
    },
]

admin = {
    "name": f"Aggregator {suffix}",
    "id": f"ADMIN-{suffix}",
    "email": f"admin{suffix}@test.hospital",
    "password": "AdminPass123!",
}


def register(h):
    return requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "hospital_name": h["name"],
            "hospital_id": h["id"],
            "contact_email": h["email"],
            "location": "Test City",
            "password": h["password"],
            "role": "ADMIN" if h is admin else "HOSPITAL",
        },
    )


def login(h):
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"hospital_id": h["id"], "password": h["password"]},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_dataset(h_id: str):
    csv_path = Path(f"./storage/datasets/{h_id}_data.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "bed_occupancy",
            "patient_count",
            "admission_rate",
            "discharge_rate",
        ])
        for i in range(120):
            day = (i // 24) + 1
            hour = i % 24
            base = 60.0 + (i % 20) * 1.5
            writer.writerow(
                [
                    f"2026-02-{(day % 28) + 1:02d}T{hour:02d}:00:00",
                    float(base),
                    float(base * 0.8),
                    float(base * 0.05),
                    float(base * 0.03),
                ]
            )
    return csv_path


print("=== Register + Login ===")
register(admin)
admin_token = login(admin)

hospital_tokens = []
for h in hospitals:
    register(h)
    token = login(h)
    hospital_tokens.append(token)

print("=== Upload, Auto-Map, Normalize, Train, Upload Weights+Masks ===")
model_ids = []
round_number = 1

for h, token in zip(hospitals, hospital_tokens):
    headers = {"Authorization": f"Bearer {token}"}

    csv_path = create_dataset(h["id"])
    with open(csv_path, "rb") as f:
        files = {"file": f}
        data = {"name": f"{h['id']} Dataset", "description": "Federated round dataset"}
        upload = requests.post(
            f"{BASE_URL}/api/datasets/upload", files=files, data=data, headers=headers
        )
    upload.raise_for_status()
    dataset_id = upload.json().get("id") or upload.json().get("dataset_id")

    auto_map = requests.post(
        f"{BASE_URL}/api/mapping/auto-map/{dataset_id}", headers=headers
    )
    auto_map.raise_for_status()

    normalize = requests.post(
        f"{BASE_URL}/api/normalization/normalize",
        json={"dataset_id": dataset_id},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    normalize.raise_for_status()

    train = requests.post(
        f"{BASE_URL}/api/training/start",
        json={
            "dataset_id": dataset_id,
            "target_column": "bed_occupancy",
            "epochs": 1,
            "epsilon": 0.5,
            "clip_norm": 1.0,
            "noise_multiplier": 0.1,
            "model_type": "tft",
        },
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    train.raise_for_status()
    model_id = train.json()["model_id"]
    model_ids.append(model_id)

    upload_weights = requests.post(
        f"{BASE_URL}/api/weights/upload",
        json={"model_id": model_id, "round_number": round_number},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    if upload_weights.status_code >= 400:
        print("Weights upload error:", upload_weights.status_code, upload_weights.text)
    upload_weights.raise_for_status()
    mask_payload = upload_weights.json()["mask_payload"]
    mask_hash = upload_weights.json().get("mask_hash")

    upload_mask = requests.post(
        f"{BASE_URL}/api/weights/masks/upload",
        json={"round_number": round_number, "mask_payload": mask_payload, "mask_hash": mask_hash},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    if upload_mask.status_code >= 400:
        print("Mask upload error:", upload_mask.status_code, upload_mask.text)
    upload_mask.raise_for_status()

print("=== Aggregate (Admin) ===")
agg = requests.post(
    f"{BASE_URL}/api/aggregation/fedavg",
    json={"round_number": round_number},
    headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
)
try:
    agg_payload = agg.json()
except ValueError:
    agg_payload = agg.text
print("Aggregation:", agg.status_code, agg_payload)
agg.raise_for_status()
agg_result = agg.json()

print("=== Latest Global Model ===")
latest = requests.get(
    f"{BASE_URL}/api/aggregation/global-model",
    headers={"Authorization": f"Bearer {admin_token}"},
)
print("Latest Global Model:", latest.status_code, latest.json())

print("=== Blockchain Audit Events ===")
audit = requests.get(
    f"{BASE_URL}/api/blockchain/audit-events?start_index=0&count=5",
    headers={"Authorization": f"Bearer {admin_token}"},
)
print("Audit:", audit.status_code, audit.json())

print("=== Global Model Download (Hospital A) ===")
model_download = requests.post(
    f"{BASE_URL}/api/model-updates/download/{round_number}",
    headers={"Authorization": f"Bearer {hospital_tokens[0]}"},
)
print("Download:", model_download.status_code, model_download.json())

print("=== Prediction (Global Model) ===")
prediction = requests.post(
    f"{BASE_URL}/api/predictions/forecast",
    json={"model_id": agg_result["global_model_id"], "forecast_horizon": 72},
    headers={"Authorization": f"Bearer {hospital_tokens[0]}", "Content-Type": "application/json"},
)
print("Prediction:", prediction.status_code, prediction.json())
