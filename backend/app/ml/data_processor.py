"""
Data preprocessing and handling for AutoML pipeline

Handles:
- Missing value imputation
- Categorical encoding
- Feature scaling
- Data validation
"""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple, Dict, List, Any
from fastapi import HTTPException


class DataProcessor:
    """
    Automated data preprocessing for regression models
    
    Processes raw CSV data into ML-ready features
    """
    
    def __init__(self):
        """Initialize processor"""
        self.imputer = None
        self.scaler = None
        self.encoders = {}  # Per-column LabelEncoders
        self.numerical_cols = []
        self.categorical_cols = []
        self.target_col = None
        self.feature_cols = []
        
    def validate_data(self, df: pd.DataFrame, target_column: str) -> None:
        """
        Validate input data
        
        Args:
            df: Input dataframe
            target_column: Target column name
        
        Raises:
            HTTPException: If data is invalid
        """
        if df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty")
        
        if target_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Target column '{target_column}' not found in dataset"
            )
        
        # Check for minimum rows
        if len(df) < 5:
            raise HTTPException(
                status_code=400,
                detail="Dataset must have at least 5 rows"
            )
        
        # Check target has variance
        target_series = pd.to_numeric(df[target_column], errors='coerce')
        if target_series.var() < 1e-12:
            raise HTTPException(
                status_code=400,
                detail="Target column has zero variance"
            )
    
    def detect_column_types(self, df: pd.DataFrame, target_column: str) -> Dict[str, List[str]]:
        """
        Detect numerical and categorical columns
        
        Args:
            df: Input dataframe
            target_column: Target column name
        
        Returns:
            Dict with 'numerical' and 'categorical' column lists
        """
        numerical = []
        categorical = []
        
        for col in df.columns:
            if col == target_column:
                continue
            
            # Try to convert to numeric
            if df[col].dtype in ['int64', 'float64']:
                numerical.append(col)
            elif df[col].dtype == 'object':
                # Check if it looks numeric
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    # If most values convert, treat as numerical
                    non_null = df[col].dropna()
                    if len(non_null) > 0:
                        convert_rate = pd.to_numeric(df[col], errors='coerce').notna().sum() / len(non_null)
                        if convert_rate > 0.8:
                            numerical.append(col)
                        else:
                            categorical.append(col)
                    else:
                        categorical.append(col)
                except:
                    categorical.append(col)
            else:
                categorical.append(col)
        
        self.numerical_cols = numerical
        self.categorical_cols = categorical
        self.target_col = target_column
        self.feature_cols = numerical + categorical
        
        return {
            'numerical': numerical,
            'categorical': categorical
        }
    
    def fit_preprocess(self, df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Fit preprocessor and transform data
        
        Args:
            df: Input dataframe
            target_column: Target column name
        
        Returns:
            Tuple of (processed_features_df, target_series)
        """
        # Validate
        self.validate_data(df, target_column)
        
        # Detect types
        self.detect_column_types(df, target_column)
        
        # Extract target
        y = pd.to_numeric(df[target_column], errors='coerce').dropna()
        
        # Work with copy
        X = df[self.feature_cols].copy()
        
        # Handle missing values in numerical columns
        if self.numerical_cols:
            X_num = X[self.numerical_cols]
            self.imputer = SimpleImputer(strategy='mean')
            X_num_imputed = self.imputer.fit_transform(X_num)
            X[self.numerical_cols] = X_num_imputed
        
        # Encode categorical columns
        X_cat = X[self.categorical_cols].copy()
        for col in self.categorical_cols:
            encoder = LabelEncoder()
            X_cat[col] = encoder.fit_transform(X_cat[col].fillna('MISSING').astype(str))
            self.encoders[col] = encoder
        
        X[self.categorical_cols] = X_cat
        
        # Scale numerical features
        if self.numerical_cols:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X[self.numerical_cols])
            X[self.numerical_cols] = X_scaled
        
        # Align X and y (remove rows with NaN in y)
        valid_idx = y.index
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]
        
        return X, y
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform new data using fitted preprocessor
        
        Args:
            df: New dataframe
        
        Returns:
            Transformed dataframe
        """
        X = df[self.feature_cols].copy()
        
        # Handle missing values
        if self.imputer and self.numerical_cols:
            X_num = X[self.numerical_cols]
            X_num_imputed = self.imputer.transform(X_num)
            X[self.numerical_cols] = X_num_imputed
        
        # Encode categorical
        X_cat = X[self.categorical_cols].copy()
        for col in self.categorical_cols:
            if col in self.encoders:
                encoder = self.encoders[col]
                X_cat[col] = encoder.transform(X_cat[col].fillna('MISSING').astype(str))
        
        X[self.categorical_cols] = X_cat
        
        # Scale numerical
        if self.scaler and self.numerical_cols:
            X_scaled = self.scaler.transform(X[self.numerical_cols])
            X[self.numerical_cols] = X_scaled
        
        return X
    
    def get_feature_info(self) -> Dict[str, Any]:
        """
        Get feature information
        
        Returns:
            Dict with feature details
        """
        return {
            'numerical_features': self.numerical_cols,
            'categorical_features': self.categorical_cols,
            'num_numerical': len(self.numerical_cols),
            'num_categorical': len(self.categorical_cols),
            'total_features': len(self.feature_cols),
            'feature_names': self.feature_cols
        }
