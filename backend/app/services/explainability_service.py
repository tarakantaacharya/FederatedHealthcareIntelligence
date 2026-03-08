"""
Model explainability service (Phase 26)
SHAP values, feature importance, attention visualization
"""
import numpy as np
import pandas as pd
import shap
from typing import Dict, List, Optional
import json
from app.ml.baseline_model import BaselineForecaster


class ExplainabilityService:
    """Service for model explainability"""
    
    @staticmethod
    def calculate_shap_values(
        model_path: str,
        data: pd.DataFrame,
        num_samples: int = 100
    ) -> Dict:
        """
        Calculate SHAP values for model predictions
        
        Args:
            model_path: Path to trained model
            data: Input data
            num_samples: Number of samples to explain
        
        Returns:
            SHAP values and base values
        """
        # Load model
        forecaster = BaselineForecaster.load_model(model_path)
        
        # Prepare features
        X = data[forecaster.feature_columns].head(num_samples)
        
        # Create SHAP explainer
        # For tree-based models, use TreeExplainer
        explainer = shap.TreeExplainer(forecaster.model)
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X)
        
        # Get expected value (base value)
        expected_value = explainer.expected_value
        
        return {
            'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
            'expected_value': float(expected_value) if isinstance(expected_value, (int, float)) else expected_value,
            'feature_names': forecaster.feature_columns,
            'num_samples': len(X)
        }
    
    @staticmethod
    def get_feature_importance(
        model_path: str,
        top_n: int = 10
    ) -> Dict:
        """
        Get feature importance from trained model
        
        Args:
            model_path: Path to trained model
            top_n: Number of top features to return
        
        Returns:
            Feature importance rankings
        """
        # Load model
        forecaster = BaselineForecaster.load_model(model_path)
        
        # Get feature importances
        importances = forecaster.model.feature_importances_
        feature_names = forecaster.feature_columns
        
        # Create importance dictionary
        importance_dict = {
            name: float(imp) 
            for name, imp in zip(feature_names, importances)
        }
        
        # Sort by importance
        sorted_features = sorted(
            importance_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return {
            'top_features': [
                {'feature': feat, 'importance': imp}
                for feat, imp in sorted_features
            ],
            'all_importances': importance_dict
        }
    
    @staticmethod
    def explain_prediction(
        model_path: str,
        sample: pd.DataFrame
    ) -> Dict:
        """
        Explain a single prediction
        
        Args:
            model_path: Path to trained model
            sample: Single sample to explain
        
        Returns:
            Prediction explanation with contributions
        """
        # Load model
        forecaster = BaselineForecaster.load_model(model_path)
        
        # Prepare features
        X = sample[forecaster.feature_columns]
        
        # Make prediction
        prediction = forecaster.predict(X)[0]
        
        # Calculate SHAP values
        explainer = shap.TreeExplainer(forecaster.model)
        shap_values = explainer.shap_values(X)
        
        # Get base value
        base_value = explainer.expected_value
        
        # Calculate feature contributions
        contributions = []
        
        for i, feature in enumerate(forecaster.feature_columns):
            shap_val = float(shap_values[0][i]) if isinstance(shap_values, np.ndarray) else float(shap_values[0][i])
            
            contributions.append({
                'feature': feature,
                'value': float(X[feature].iloc[0]),
                'shap_value': shap_val,
                'contribution': shap_val
            })
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        return {
            'prediction': float(prediction),
            'base_value': float(base_value),
            'contributions': contributions,
            'top_positive_contributors': [
                c for c in contributions if c['contribution'] > 0
            ][:5],
            'top_negative_contributors': [
                c for c in contributions if c['contribution'] < 0
            ][:5]
        }
    
    @staticmethod
    def analyze_category_impact(
        model_path: str,
        data: pd.DataFrame,
        category: str
    ) -> Dict:
        """
        Analyze impact of treatment category fields
        
        Args:
            model_path: Path to trained model
            data: Input data
            category: Category name (icu, emergency, etc.)
        
        Returns:
            Category impact analysis
        """
        # Load model
        forecaster = BaselineForecaster.load_model(model_path)
        
        # Find category fields
        category_fields = [
            col for col in forecaster.feature_columns 
            if col.startswith(f"{category}_")
        ]
        
        if not category_fields:
            return {
                'category': category,
                'error': 'No fields found for this category'
            }
        
        # Calculate SHAP values
        X = data[forecaster.feature_columns]
        explainer = shap.TreeExplainer(forecaster.model)
        shap_values = explainer.shap_values(X)
        
        # Get indices of category fields
        category_indices = [
            forecaster.feature_columns.index(field) 
            for field in category_fields
        ]
        
        # Calculate category impact
        if isinstance(shap_values, np.ndarray):
            category_shap = shap_values[:, category_indices]
        else:
            category_shap = np.array([[shap_values[i][idx] for idx in category_indices] for i in range(len(shap_values))])
        
        # Calculate statistics
        mean_impact = np.mean(np.abs(category_shap), axis=0)
        total_category_impact = np.sum(np.abs(category_shap), axis=1)
        
        field_impacts = []
        for i, field in enumerate(category_fields):
            field_impacts.append({
                'field': field,
                'mean_absolute_impact': float(mean_impact[i]),
                'percentage_of_category': float(mean_impact[i] / np.sum(mean_impact) * 100) if np.sum(mean_impact) > 0 else 0
            })
        
        # Sort by impact
        field_impacts.sort(key=lambda x: x['mean_absolute_impact'], reverse=True)
        
        return {
            'category': category,
            'num_fields': len(category_fields),
            'mean_total_impact': float(np.mean(total_category_impact)),
            'field_impacts': field_impacts,
            'top_impactful_fields': field_impacts[:5]
        }
    
    @staticmethod
    def generate_explanation_report(
        model_path: str,
        data: pd.DataFrame,
        sample_size: int = 100
    ) -> Dict:
        """
        Generate comprehensive explanation report
        
        Args:
            model_path: Path to trained model
            data: Input data
            sample_size: Number of samples to analyze
        
        Returns:
            Comprehensive explainability report
        """
        # Feature importance
        importance = ExplainabilityService.get_feature_importance(model_path, top_n=15)
        
        # SHAP values
        shap_data = ExplainabilityService.calculate_shap_values(
            model_path, data, num_samples=sample_size
        )
        
        # Category analysis (if categories present)
        categories = ['icu', 'emergency', 'opd', 'ipd', 'surgery', 'pediatrics', 'cardiology']
        category_analyses = {}
        
        for category in categories:
            try:
                analysis = ExplainabilityService.analyze_category_impact(
                    model_path, data, category
                )
                if 'error' not in analysis:
                    category_analyses[category] = analysis
            except:
                continue
        
        return {
            'model_path': model_path,
            'num_samples_analyzed': sample_size,
            'feature_importance': importance,
            'shap_analysis': {
                'expected_value': shap_data['expected_value'],
                'num_features': len(shap_data['feature_names'])
            },
            'category_analyses': category_analyses,
            'generated_at': pd.Timestamp.now().isoformat()
        }
