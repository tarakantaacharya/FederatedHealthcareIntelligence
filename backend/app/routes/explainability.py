"""
Model explainability routes (Phase 26)
SHAP, feature importance, category impact
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.model_weights import ModelWeights
from app.models.dataset import Dataset
from app.utils.auth import require_role
from app.services.explainability_service import ExplainabilityService
import pandas as pd

router = APIRouter()


@router.get("/feature-importance/{model_id}")
async def get_feature_importance(
    model_id: int,
    top_n: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get feature importance from model
    
    - **model_id**: Model ID
    - **top_n**: Number of top features
    
    Returns ranked list of most important features.
    """
    # Get model
    model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify access
    hospital = current_user["db_object"]
    if model.hospital_id and model.hospital_id != hospital.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    importance = ExplainabilityService.get_feature_importance(
        model.model_path, top_n=top_n
    )
    
    return importance


@router.post("/explain-prediction/{model_id}")
async def explain_prediction(
    model_id: int,
    dataset_id: int,
    sample_index: int = 0,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Explain a single prediction with SHAP values
    
    - **model_id**: Model ID
    - **dataset_id**: Dataset ID
    - **sample_index**: Row index to explain
    
    Returns SHAP-based explanation with feature contributions.
    """
    # Get model
    model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get dataset
    hospital = current_user["db_object"]
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Load data
    data = pd.read_csv(dataset.file_path)
    
    if sample_index >= len(data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sample index {sample_index} out of range"
        )
    
    sample = data.iloc[[sample_index]]
    
    explanation = ExplainabilityService.explain_prediction(
        model.model_path, sample
    )
    
    return explanation


@router.get("/category-impact/{model_id}/{category}")
async def analyze_category_impact(
    model_id: int,
    category: str,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Analyze impact of treatment category fields
    
    - **model_id**: Model ID
    - **category**: Category name (icu, emergency, opd, ipd, surgery, pediatrics, cardiology)
    - **dataset_id**: Dataset ID
    
    Returns impact analysis for all fields in the category.
    """
    # Get model
    model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get dataset
    hospital = current_user["db_object"]
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Load data
    data = pd.read_csv(dataset.file_path)
    
    analysis = ExplainabilityService.analyze_category_impact(
        model.model_path, data, category
    )
    
    return analysis


@router.get("/comprehensive-report/{model_id}")
async def get_comprehensive_report(
    model_id: int,
    dataset_id: int,
    sample_size: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate comprehensive explainability report
    
    - **model_id**: Model ID
    - **dataset_id**: Dataset ID
    - **sample_size**: Number of samples to analyze
    
    **Includes:**
    - Feature importance rankings
    - SHAP value analysis
    - Category impact analysis
    - Top contributors
    """
    # Get model
    model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get dataset
    hospital = current_user["db_object"]
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Load data
    data = pd.read_csv(dataset.file_path)
    
    report = ExplainabilityService.generate_explanation_report(
        model.model_path, data, sample_size=sample_size
    )
    
    return report
