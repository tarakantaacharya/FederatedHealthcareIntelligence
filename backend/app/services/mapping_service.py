"""
Mapping service
"""
from sqlalchemy.orm import Session
from app.models.schema_mappings import SchemaMapping
from app.models.dataset import Dataset


class MappingService:
    @staticmethod
    def get_dataset_mapping(dataset_id: int, db: Session) -> dict:
        mappings = db.query(SchemaMapping).filter(SchemaMapping.dataset_id == dataset_id).all()
        return {
            'dataset_id': dataset_id,
            'mappings': [
                {
                    'original_column': m.original_column,
                    'canonical_field': m.canonical_field,
                    'confidence': m.confidence
                }
                for m in mappings
            ]
        }
    
    @staticmethod
    def save_mapping(dataset_id: int, original_column: str, canonical_field: str, confidence: float, hospital_id: int, db: Session):
        mapping = SchemaMapping(
            dataset_id=dataset_id,
            original_column=original_column,
            canonical_field=canonical_field,
            confidence=confidence,
            hospital_id=hospital_id
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        return mapping
