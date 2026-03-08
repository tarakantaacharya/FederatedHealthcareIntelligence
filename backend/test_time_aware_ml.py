from app.database import SessionLocal
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.services.training_service import TrainingService
from types import SimpleNamespace
import traceback

db = SessionLocal()
try:
    h = db.query(Hospital).first()
    d = db.query(Dataset).filter(Dataset.hospital_id == h.id).first()
    if not h or not d:
        print('ERROR: No hospital or dataset found')
    else:
        print('[TEST] Time-Aware ML Training with Temporal Features')
        print(f'Hospital: {h.hospital_id}, Dataset: {d.id}')
        print()
        req = SimpleNamespace(training_type='LOCAL', model_architecture='ML_REGRESSION', target_column='bed_occupancy', batch_size=16)
        try:
            result = TrainingService.train_local_model(
                db=db,
                hospital=h,
                dataset_id=d.id,
                target_column='bed_occupancy',
                training_request=req,
                epochs=1,
                batch_size=16
            )
            print('[SUCCESS] Time-aware ML training completed!')
            best_model = result.get('best_model')
            best_r2 = result.get('test_r2', 'N/A')
            print(f'Best model: {best_model}')
            print(f'Best R2: {best_r2}')
        except Exception as e:
            print(f'[ERROR] {type(e).__name__}: {str(e)[:200]}')
            traceback.print_exc()
finally:
    db.close()
