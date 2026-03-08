"""Check AYURVEDA hospital details"""
from app.database import SessionLocal
from app.models.hospital import Hospital

db = SessionLocal()
h = db.query(Hospital).filter(Hospital.hospital_id == 'AYURVEDA').first()
if h:
    print(f"✅ Hospital found: {h.hospital_name}")
    print(f"   ID: {h.id}")
    print(f"   Federated allowed: {h.is_allowed_federated}")
else:
    print("❌ Hospital NOT FOUND")
db.close()
