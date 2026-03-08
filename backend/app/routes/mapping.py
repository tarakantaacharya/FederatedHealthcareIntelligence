"""
Schema mapping routes (Phase 9)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.models.dataset import Dataset
from app.schemas.mapping_schema import AutoMapResponse, ManualMappingRequest, Mapping
from app.services.mapping_service import MappingService
from app.models.schema_mappings import SchemaMapping
from app.services.canonical_field_service import CanonicalFieldService
import json
import difflib
from app.config import get_settings

router = APIRouter()


def calculate_confidence(source_col: str, target_field: str) -> float:
    """Calculate confidence score between 0 and 1 using string similarity"""
    source_lower = source_col.lower().strip()
    target_lower = target_field.lower().strip()
    
    # Direct match
    if source_lower == target_lower:
        return 1.0
    
    # Substring match
    if source_lower in target_lower or target_lower in source_lower:
        return 0.9
    
    # Fuzzy match using difflib
    similarity = difflib.SequenceMatcher(None, source_lower, target_lower).ratio()
    return round(similarity, 2)


def auto_map_columns(dataset_columns: List[str], canonical_fields: List[str]) -> Tuple[List[Mapping], List[str]]:
    """
    Automatically map dataset columns to canonical fields.
    Returns: (list of Mapping objects, list of unmapped column names)
    """
    mappings = []
    mapped_columns = set()
    
    for col in dataset_columns:
        best_match = None
        best_confidence = 0.0
        
        for canonical_field in canonical_fields:
            confidence = calculate_confidence(col, canonical_field)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = canonical_field
        
        # Only include mapping if confidence is above 0.3
        if best_match and best_confidence >= 0.3:
            mapping = Mapping(
                original_column=col,
                canonical_field=best_match,
                confidence=best_confidence
            )
            mappings.append(mapping)
            mapped_columns.add(col)
    
    unmapped = [col for col in dataset_columns if col not in mapped_columns]
    return mappings, unmapped


@router.post("/auto-map/{dataset_id}", response_model=AutoMapResponse)
async def auto_map_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Auto-map dataset columns to canonical schema"""
    hospital = current_user["db_object"]
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Parse column names from dataset
    try:
        column_names = json.loads(dataset.column_names) if dataset.column_names else []
    except json.JSONDecodeError:
        column_names = []
    
    if not column_names:
        return AutoMapResponse(
            dataset_id=dataset_id,
            mappings=[],
            unmapped_columns=[],
            total_columns=0,
            mapped_count=0,
            unmapped_count=0,
            mapping_success_rate=0.0
        )
    
    active_fields = CanonicalFieldService.get_all_active_fields(db)
    canonical_field_names = [field.field_name for field in active_fields]
    if not canonical_field_names:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active canonical fields configured"
        )

    # Perform auto-mapping
    mappings, unmapped_columns = auto_map_columns(column_names, canonical_field_names)
    
    # Delete existing mappings for this dataset first (to avoid duplicates)
    from app.models.schema_mappings import SchemaMapping
    db.query(SchemaMapping).filter(SchemaMapping.dataset_id == dataset_id).delete()
    db.commit()
    
    # Save new mappings to database
    for mapping in mappings:
        MappingService.save_mapping(
            dataset_id=dataset_id,
            original_column=mapping.original_column,
            canonical_field=mapping.canonical_field,
            confidence=mapping.confidence,
            hospital_id=hospital.id,
            db=db
        )
    
    # Calculate metrics
    total_columns = len(column_names)
    mapped_count = len(mappings)
    unmapped_count = len(unmapped_columns)
    mapping_success_rate = (mapped_count / total_columns * 100) if total_columns > 0 else 0.0
    
    return AutoMapResponse(
        dataset_id=dataset_id,
        mappings=mappings,
        unmapped_columns=unmapped_columns,
        total_columns=total_columns,
        mapped_count=mapped_count,
        unmapped_count=unmapped_count,
        mapping_success_rate=mapping_success_rate
    )


@router.post("/manual")
async def save_manual_mapping(
    request: ManualMappingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Save manual column mappings"""
    hospital = current_user["db_object"]

    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    try:
        dataset_columns = json.loads(dataset.column_names) if dataset.column_names else []
    except json.JSONDecodeError:
        dataset_columns = []

    if not dataset_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset columns not available for mapping"
        )

    active_fields = CanonicalFieldService.get_all_active_fields(db)
    active_field_names = {field.field_name for field in active_fields}

    saved_count = 0
    for original_column, canonical_field in request.mappings.items():
        if original_column not in dataset_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{original_column}' does not exist in dataset"
            )

        if canonical_field not in active_field_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Canonical field '{canonical_field}' is not active"
            )

        existing = db.query(SchemaMapping).filter(
            SchemaMapping.dataset_id == request.dataset_id,
            SchemaMapping.original_column == original_column
        ).first()

        if existing:
            existing.canonical_field = canonical_field
            existing.confidence = 1.0
            existing.hospital_id = hospital.id
        else:
            db.add(SchemaMapping(
                dataset_id=request.dataset_id,
                original_column=original_column,
                canonical_field=canonical_field,
                confidence=1.0,
                hospital_id=hospital.id
            ))

        saved_count += 1

    db.commit()

    return {
        "status": "success",
        "dataset_id": request.dataset_id,
        "saved_count": saved_count
    }


@router.get("/dataset/{dataset_id}")
async def get_dataset_mapping(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Get saved mappings for a dataset"""
    hospital = current_user["db_object"]
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    return MappingService.get_dataset_mapping(dataset_id, db)
