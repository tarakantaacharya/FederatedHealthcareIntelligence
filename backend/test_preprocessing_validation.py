#!/usr/bin/env python3
"""Validate float32 preprocessing and TFT training start."""
import csv
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"

hospital_id = "FLOAT-TEST-001"
password = "FloatPass123!"

# Register hospital (ignore if exists)
requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "hospital_name": "Float Test Hospital",
        "hospital_id": hospital_id,
        "contact_email": "float@test.hospital",
        "location": "Test City",
        "password": password,
        "role": "HOSPITAL",
    },
)

login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"hospital_id": hospital_id, "password": password},
)
login.raise_for_status()

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create float-heavy dataset
csv_path = Path("./storage/datasets/float_validation.csv")
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

with open(csv_path, "rb") as f:
    files = {"file": f}
    data = {"name": "Float Validation", "description": "Float preprocessing test"}
    upload = requests.post(
        f"{BASE_URL}/api/datasets/upload", files=files, data=data, headers=headers
    )

upload.raise_for_status()
dataset_id = upload.json().get("id") or upload.json().get("dataset_id")

payload = {
    "dataset_id": dataset_id,
    "target_column": "bed_occupancy",
    "epochs": 1,
    "epsilon": 0.5,
    "clip_norm": 1.0,
    "noise_multiplier": 0.1,
    "model_type": "tft",
}

train = requests.post(
    f"{BASE_URL}/api/training/start",
    json=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)

print("Training status:", train.status_code)
print("Training response:", train.json())
