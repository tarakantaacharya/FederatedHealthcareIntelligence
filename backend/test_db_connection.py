"""Simple test to verify database connection and ORM alignment after .env fix"""
import sys
sys.path.insert(0, ".")

from sqlalchemy import inspect
from app.database import engine, SessionLocal
# Import models in dependency order (same as main.py)
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.training_rounds import TrainingRound
from app.models.model_weights import ModelWeights
from app.models.model_mask import ModelMask
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.models.alerts import Alert
from app.models.schema_mappings import SchemaMapping
from app.models.schema_versions import SchemaVersion
from app.models.privacy_budget import PrivacyBudget
from app.models.model_governance import ModelGovernance
from app.models.admin import Admin
from app.models.notification import Notification
from app.models.notification_preferences import NotificationPreference
from app.models.model_registry import ModelRegistry
from app.models.blockchain import Blockchain
from app.models.prediction_record import PredictionRecord
from app.models.hospitals_profile import HospitalProfile

def test_connection():
    """Test database connection and schema"""
    print("\n" + "="*60)
    print("DATABASE CONNECTION TEST - POST .ENV FIX")
    print("="*60)
    
    # 1. Check engine connection
    print(f"\n1️⃣ Engine URL: {engine.url}")
    
    # 2. Get inspector
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n2️⃣ Tables in database: {len(tables)}")
    print(f"   Tables: {', '.join(sorted(tables))}")
    
    # 3. Check hospitals table columns
    if 'hospitals' in tables:
        hospitals_cols = [col['name'] for col in inspector.get_columns('hospitals')]
        print(f"\n3️⃣ Hospitals table columns ({len(hospitals_cols)}):")
        print(f"   {', '.join(hospitals_cols)}")
        print(f"\n   ✅ Has verification_status: {'verification_status' in hospitals_cols}")
        print(f"   ✅ Has is_allowed_federated: {'is_allowed_federated' in hospitals_cols}")
    
    # 4. Check model_weights table columns
    if 'model_weights' in tables:
        weights_cols = [col['name'] for col in inspector.get_columns('model_weights')]
        print(f"\n4️⃣ Model_weights table columns ({len(weights_cols)}):")
        print(f"   {', '.join(weights_cols)}")
        print(f"\n   ✅ Has training_type: {'training_type' in weights_cols}")
        print(f"   ✅ Has model_architecture: {'model_architecture' in weights_cols}")
    
    # 5. Test ORM query on hospitals
    print(f"\n5️⃣ Testing ORM query on Hospital model...")
    try:
        db = SessionLocal()
        # Try to query with the problematic column
        result = db.query(Hospital).filter(Hospital.verification_status == 'pending').all()
        print(f"   ✅ ORM Query SUCCESS - Found {len(result)} hospitals with pending verification")
        db.close()
    except Exception as e:
        print(f"   ❌ ORM Query FAILED: {e}")
        return False
    
    # 6. Test ORM query on model_weights
    print(f"\n6️⃣ Testing ORM query on ModelWeights model...")
    try:
        db = SessionLocal()
        # Try to query with the problematic columns
        result = db.query(ModelWeights).filter(ModelWeights.training_type == 'tft').all()
        print(f"   ✅ ORM Query SUCCESS - Found {len(result)} weights with TFT training_type")
        db.close()
    except Exception as e:
        print(f"   ❌ ORM Query FAILED: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL DATABASE TESTS PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
