"""
Category Specialization Service (Phase 33)
Hospital category-specific models (Pediatric, ICU, Cardiology, etc.)
"""
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import pickle
import os
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class HospitalCategory:
    """Hospital category constants"""
    GENERAL = "general"
    PEDIATRIC = "pediatric"
    ICU = "icu"
    CARDIOLOGY = "cardiology"
    EMERGENCY = "emergency"
    MATERNITY = "maternity"


class CategorySpecializationService:
    """Service for category-specific model training and prediction"""
    
    # Category-specific feature importance weights
    CATEGORY_FEATURES = {
        HospitalCategory.PEDIATRIC: {
            'age_0_18': 2.0,
            'pediatric_beds': 2.0,
            'vaccination_rate': 1.5,
            'seasonal_illness': 1.8
        },
        HospitalCategory.ICU: {
            'critical_beds': 2.5,
            'ventilator_capacity': 2.0,
            'mortality_rate': 1.5,
            'avg_stay_days': 1.8
        },
        HospitalCategory.CARDIOLOGY: {
            'cardiac_beds': 2.0,
            'cardiac_surgery_rate': 2.5,
            'age_50_plus': 1.8,
            'comorbidity_index': 1.5
        },
        HospitalCategory.EMERGENCY: {
            'er_beds': 2.5,
            'trauma_cases': 2.0,
            'ambulance_arrivals': 2.0,
            'triage_level_1': 1.8
        },
        HospitalCategory.MATERNITY: {
            'maternity_beds': 2.5,
            'birth_rate': 2.0,
            'c_section_rate': 1.5,
            'nicu_capacity': 1.8
        }
    }
    
    @staticmethod
    def detect_category(df: pd.DataFrame) -> str:
        """
        Auto-detect hospital category from dataset columns
        
        Args:
            df: Dataset DataFrame
        
        Returns:
            Detected category string
        """
        columns = set(df.columns)
        
        # Check for category-specific columns
        if any(col in columns for col in ['pediatric_beds', 'vaccination_rate', 'age_0_18']):
            return HospitalCategory.PEDIATRIC
        elif any(col in columns for col in ['critical_beds', 'ventilator_capacity', 'icu_beds']):
            return HospitalCategory.ICU
        elif any(col in columns for col in ['cardiac_beds', 'cardiac_surgery_rate', 'cardiology']):
            return HospitalCategory.CARDIOLOGY
        elif any(col in columns for col in ['er_beds', 'trauma_cases', 'emergency']):
            return HospitalCategory.EMERGENCY
        elif any(col in columns for col in ['maternity_beds', 'birth_rate', 'nicu']):
            return HospitalCategory.MATERNITY
        else:
            return HospitalCategory.GENERAL
    
    @staticmethod
    def engineer_category_features(
        df: pd.DataFrame,
        category: str
    ) -> pd.DataFrame:
        """
        Apply category-specific feature engineering
        
        Args:
            df: Input DataFrame
            category: Hospital category
        
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        if category == HospitalCategory.PEDIATRIC:
            # Pediatric-specific features
            if 'age_0_18' in df.columns and 'total_patients' in df.columns:
                df['pediatric_ratio'] = df['age_0_18'] / (df['total_patients'] + 1)
            if 'vaccination_rate' in df.columns:
                df['vaccination_risk'] = 1 - df['vaccination_rate']
        
        elif category == HospitalCategory.ICU:
            # ICU-specific features
            if 'critical_beds' in df.columns and 'total_beds' in df.columns:
                df['icu_capacity_ratio'] = df['critical_beds'] / (df['total_beds'] + 1)
            if 'ventilator_capacity' in df.columns and 'critical_beds' in df.columns:
                df['ventilator_per_bed'] = df['ventilator_capacity'] / (df['critical_beds'] + 1)
        
        elif category == HospitalCategory.CARDIOLOGY:
            # Cardiology-specific features
            if 'age_50_plus' in df.columns and 'total_patients' in df.columns:
                df['elderly_ratio'] = df['age_50_plus'] / (df['total_patients'] + 1)
            if 'cardiac_surgery_rate' in df.columns:
                df['high_risk_cardiac'] = (df['cardiac_surgery_rate'] > 0.3).astype(int)
        
        elif category == HospitalCategory.EMERGENCY:
            # Emergency-specific features
            if 'trauma_cases' in df.columns and 'total_patients' in df.columns:
                df['trauma_ratio'] = df['trauma_cases'] / (df['total_patients'] + 1)
            if 'ambulance_arrivals' in df.columns:
                df['emergency_pressure'] = df['ambulance_arrivals'] / 24  # per hour
        
        elif category == HospitalCategory.MATERNITY:
            # Maternity-specific features
            if 'birth_rate' in df.columns and 'maternity_beds' in df.columns:
                df['births_per_bed'] = df['birth_rate'] / (df['maternity_beds'] + 1)
            if 'c_section_rate' in df.columns:
                df['high_risk_delivery'] = (df['c_section_rate'] > 0.35).astype(int)
        
        return df
    
    @staticmethod
    def train_category_model(
        db: Session,
        hospital_id: int,
        dataset_id: int,
        category: Optional[str] = None
    ) -> Dict:
        """
        Train category-specific model
        
        Args:
            db: Database session
            hospital_id: Hospital ID
            dataset_id: Dataset ID
            category: Hospital category (auto-detected if None)
        
        Returns:
            Training results dictionary
        """
        # Load dataset
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.hospital_id == hospital_id
        ).first()
        
        if not dataset:
            raise ValueError("Dataset not found")
        
        file_path = os.path.normpath(dataset.file_path)
        df = pd.read_csv(file_path)
        
        # Auto-detect category if not provided
        if not category:
            category = CategorySpecializationService.detect_category(df)
        
        logger.info(f"Training {category} model for hospital {hospital_id}")
        
        # Engineer category-specific features
        df = CategorySpecializationService.engineer_category_features(df, category)
        
        # Prepare features (numeric only)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Assume last column is target
        if len(numeric_cols) < 2:
            raise ValueError("Insufficient numeric columns for training")
        
        target_col = numeric_cols[-1]
        feature_cols = numeric_cols[:-1]
        
        X = df[feature_cols].fillna(0).values
        y = df[target_col].fillna(0).values
        
        # Train category-specific Random Forest
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        
        # Save model
        model_dir = os.path.join(settings.MODEL_DIR, f"hospital_{hospital_id}", category)
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f"model_{category}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Calculate feature importance
        feature_importance = dict(zip(feature_cols, model.feature_importances_))
        
        return {
            'category': category,
            'model_path': model_path,
            'num_features': len(feature_cols),
            'num_samples': len(df),
            'feature_importance': feature_importance,
            'success': True
        }
    
    @staticmethod
    def predict_with_category_model(
        hospital_id: int,
        category: str,
        features: Dict[str, float]
    ) -> Dict:
        """
        Make prediction using category-specific model
        
        Args:
            hospital_id: Hospital ID
            category: Hospital category
            features: Input features dictionary
        
        Returns:
            Prediction results
        """
        model_path = os.path.join(
            settings.MODEL_DIR,
            f"hospital_{hospital_id}",
            category,
            f"model_{category}.pkl"
        )
        
        if not os.path.exists(model_path):
            raise ValueError(f"Model not found for category: {category}")
        
        # Load model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Prepare input
        feature_values = list(features.values())
        X = np.array(feature_values).reshape(1, -1)
        
        # Predict
        prediction = model.predict(X)[0]
        
        return {
            'category': category,
            'prediction': float(prediction),
            'features_used': list(features.keys())
        }
