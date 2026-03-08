"""Test which route import hangs"""
from fastapi import FastAPI
from app.database import engine, Base
from app.models.hospital import Hospital
from app.models.dataset import Dataset

print("TEST: Models imported OK")

# Try importing routes one by one
routes_to_test = [
    "auth",
    "admin_auth", 
    "hospitals",
    "datasets",
    "training",
    "aggregation",
    "weights",
    "model_updates",
    "rounds",
    "schema",
    "mapping",
]

for route_name in routes_to_test:
    print(f"TEST: Importing app.routes.{route_name}...")
    try:
        __import__(f"app.routes.{route_name}")
        print(f"TEST: [OK] {route_name}")
    except Exception as e:
        print(f"TEST: [FAIL] {route_name}: {e}")
        break

print("TEST: All routes imported!")
