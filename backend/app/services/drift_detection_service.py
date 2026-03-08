"""
Data drift detection service (Phase 24)
Monitors data distribution changes and triggers retraining
"""
import numpy as np
import pandas as pd
import os
from scipy import stats
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.hospital import Hospital


class DriftType:
    """Types of drift"""
    COVARIATE_SHIFT = 'covariate_shift'  # Input distribution changes
    PRIOR_PROBABILITY_SHIFT = 'prior_probability_shift'  # Target distribution changes
    CONCEPT_DRIFT = 'concept_drift'  # Relationship between X and Y changes


class DriftSeverity:
    """Drift severity levels"""
    NONE = 'none'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class DriftDetectionService:
    """Service for detecting data drift"""
    
    # Statistical test thresholds
    KS_TEST_THRESHOLD = 0.05  # Kolmogorov-Smirnov test p-value
    CHI2_THRESHOLD = 0.05  # Chi-squared test p-value
    PSI_THRESHOLD_LOW = 0.1  # Population Stability Index
    PSI_THRESHOLD_MEDIUM = 0.2
    PSI_THRESHOLD_HIGH = 0.25
    
    @staticmethod
    def calculate_psi(
        expected: np.ndarray,
        actual: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI)
        
        PSI measures distribution shift between two datasets
        
        Args:
            expected: Reference distribution (training data)
            actual: Current distribution (new data)
            bins: Number of bins for discretization
        
        Returns:
            PSI value (0 = no drift, >0.25 = significant drift)
        """
        # Create bins based on expected distribution
        breakpoints = np.linspace(
            np.percentile(expected, 0),
            np.percentile(expected, 100),
            bins + 1
        )
        
        # Calculate distributions
        expected_percents = np.histogram(expected, bins=breakpoints)[0] / len(expected)
        actual_percents = np.histogram(actual, bins=breakpoints)[0] / len(actual)
        
        # Avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        # Calculate PSI
        psi = np.sum(
            (actual_percents - expected_percents) * 
            np.log(actual_percents / expected_percents)
        )
        
        return psi
    
    @staticmethod
    def ks_test(
        reference: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float]:
        """
        Perform Kolmogorov-Smirnov test
        
        Tests if two samples come from the same distribution
        
        Args:
            reference: Reference sample
            current: Current sample
        
        Returns:
            Tuple of (statistic, p_value)
        """
        statistic, p_value = stats.ks_2samp(reference, current)
        return statistic, p_value
    
    @staticmethod
    def detect_feature_drift(
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        feature_columns: List[str]
    ) -> Dict:
        """
        Detect drift in feature distributions
        
        Args:
            reference_data: Reference dataset (training data)
            current_data: Current dataset (new data)
            feature_columns: List of feature columns to check
        
        Returns:
            Drift detection results per feature
        """
        drift_results = {}
        
        for feature in feature_columns:
            if feature not in reference_data.columns or feature not in current_data.columns:
                continue
            
            ref_values = reference_data[feature].dropna().values
            curr_values = current_data[feature].dropna().values
            
            if len(ref_values) == 0 or len(curr_values) == 0:
                continue
            
            # Calculate PSI
            psi = DriftDetectionService.calculate_psi(ref_values, curr_values)
            
            # Perform KS test
            ks_stat, ks_pvalue = DriftDetectionService.ks_test(ref_values, curr_values)
            
            # Determine drift severity
            if psi < DriftDetectionService.PSI_THRESHOLD_LOW:
                severity = DriftSeverity.NONE
            elif psi < DriftDetectionService.PSI_THRESHOLD_MEDIUM:
                severity = DriftSeverity.LOW
            elif psi < DriftDetectionService.PSI_THRESHOLD_HIGH:
                severity = DriftSeverity.MEDIUM
            else:
                severity = DriftSeverity.CRITICAL
            
            # Statistical significance
            is_significant = ks_pvalue < DriftDetectionService.KS_TEST_THRESHOLD
            
            drift_results[feature] = {
                'psi': float(psi),
                'ks_statistic': float(ks_stat),
                'ks_pvalue': float(ks_pvalue),
                'is_significant': is_significant,
                'severity': severity,
                'drift_detected': is_significant and severity != DriftSeverity.NONE
            }
        
        return drift_results
    
    @staticmethod
    def detect_target_drift(
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_column: str
    ) -> Dict:
        """
        Detect drift in target variable distribution
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            target_column: Target column name
        
        Returns:
            Target drift detection results
        """
        if target_column not in reference_data.columns or target_column not in current_data.columns:
            return {'error': 'Target column not found'}
        
        ref_values = reference_data[target_column].dropna().values
        curr_values = current_data[target_column].dropna().values
        
        # Calculate PSI
        psi = DriftDetectionService.calculate_psi(ref_values, curr_values)
        
        # KS test
        ks_stat, ks_pvalue = DriftDetectionService.ks_test(ref_values, curr_values)
        
        # Calculate mean shift
        ref_mean = np.mean(ref_values)
        curr_mean = np.mean(curr_values)
        mean_shift_percent = ((curr_mean - ref_mean) / ref_mean) * 100 if ref_mean != 0 else 0
        
        # Determine severity
        if psi < DriftDetectionService.PSI_THRESHOLD_LOW:
            severity = DriftSeverity.NONE
        elif psi < DriftDetectionService.PSI_THRESHOLD_MEDIUM:
            severity = DriftSeverity.LOW
        elif psi < DriftDetectionService.PSI_THRESHOLD_HIGH:
            severity = DriftSeverity.MEDIUM
        else:
            severity = DriftSeverity.CRITICAL
        
        return {
            'target_column': target_column,
            'psi': float(psi),
            'ks_statistic': float(ks_stat),
            'ks_pvalue': float(ks_pvalue),
            'ref_mean': float(ref_mean),
            'current_mean': float(curr_mean),
            'mean_shift_percent': float(mean_shift_percent),
            'severity': severity,
            'drift_detected': ks_pvalue < DriftDetectionService.KS_TEST_THRESHOLD
        }
    
    @staticmethod
    def comprehensive_drift_check(
        hospital_id: int,
        reference_dataset_id: int,
        current_dataset_id: int,
        db: Session
    ) -> Dict:
        """
        Perform comprehensive drift detection
        
        Args:
            hospital_id: Hospital ID
            reference_dataset_id: Reference dataset ID (training data)
            current_dataset_id: Current dataset ID (new data)
            db: Database session
        
        Returns:
            Comprehensive drift report
        """
        # Load datasets
        ref_dataset = db.query(Dataset).filter(
            Dataset.id == reference_dataset_id,
            Dataset.hospital_id == hospital_id
        ).first()
        
        curr_dataset = db.query(Dataset).filter(
            Dataset.id == current_dataset_id,
            Dataset.hospital_id == hospital_id
        ).first()
        
        if not ref_dataset or not curr_dataset:
            return {'error': 'Dataset not found'}
        
        # Load data
        ref_path = os.path.normpath(ref_dataset.file_path)
        curr_path = os.path.normpath(curr_dataset.file_path)
        ref_data = pd.read_csv(ref_path)
        curr_data = pd.read_csv(curr_path)
        
        # Get feature columns (exclude target and metadata)
        exclude_cols = ['timestamp', 'bed_occupancy', 'hospital_id']
        feature_cols = [
            col for col in ref_data.columns 
            if col not in exclude_cols and col in curr_data.columns
        ]
        
        # Detect feature drift
        feature_drift = DriftDetectionService.detect_feature_drift(
            ref_data, curr_data, feature_cols
        )
        
        # Detect target drift
        target_drift = DriftDetectionService.detect_target_drift(
            ref_data, curr_data, 'bed_occupancy'
        )
        
        # Count drifted features
        drifted_features = [
            feat for feat, result in feature_drift.items() 
            if result['drift_detected']
        ]
        
        # Determine overall severity
        max_severity = DriftSeverity.NONE
        for result in feature_drift.values():
            if result['severity'] == DriftSeverity.CRITICAL:
                max_severity = DriftSeverity.CRITICAL
                break
            elif result['severity'] == DriftSeverity.MEDIUM and max_severity != DriftSeverity.CRITICAL:
                max_severity = DriftSeverity.MEDIUM
            elif result['severity'] == DriftSeverity.LOW and max_severity == DriftSeverity.NONE:
                max_severity = DriftSeverity.LOW
        
        # Consider target drift
        if target_drift.get('severity') == DriftSeverity.CRITICAL:
            max_severity = DriftSeverity.CRITICAL
        
        # Retraining recommendation
        should_retrain = (
            max_severity in [DriftSeverity.MEDIUM, DriftSeverity.CRITICAL] or
            len(drifted_features) > len(feature_cols) * 0.3  # >30% features drifted
        )
        
        return {
            'hospital_id': hospital_id,
            'reference_dataset_id': reference_dataset_id,
            'current_dataset_id': current_dataset_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'feature_drift': feature_drift,
            'target_drift': target_drift,
            'summary': {
                'total_features_checked': len(feature_cols),
                'drifted_features_count': len(drifted_features),
                'drift_percentage': (len(drifted_features) / len(feature_cols) * 100) if feature_cols else 0,
                'drifted_features': drifted_features,
                'overall_severity': max_severity,
                'should_retrain': should_retrain,
                'recommendation': 'RETRAIN_RECOMMENDED' if should_retrain else 'NO_ACTION_NEEDED'
            }
        }
    
    @staticmethod
    def auto_trigger_retraining(
        drift_report: Dict,
        db: Session
    ) -> Dict:
        """
        Automatically trigger retraining based on drift
        
        Args:
            drift_report: Drift detection report
            db: Database session
        
        Returns:
            Retraining trigger result
        """
        if not drift_report['summary']['should_retrain']:
            return {
                'triggered': False,
                'reason': 'Drift below retraining threshold'
            }
        
        hospital_id = drift_report['hospital_id']
        current_dataset_id = drift_report['current_dataset_id']
        
        # Trigger retraining
        from app.services.training_service import TrainingService
        from app.services.round_service import RoundService
        from app.models.hospital import Hospital
        
        try:
            current_round = RoundService.require_active_round_with_target(db)
            hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hospital:
                return {
                    'triggered': False,
                    'error': 'Hospital not found'
                }

            # Start local training on new dataset
            training_result = TrainingService.train_local_model(
                db=db,
                hospital=hospital,
                dataset_id=current_dataset_id,
                target_column=current_round.target_column
            )
            
            return {
                'triggered': True,
                'reason': f"Drift severity: {drift_report['summary']['overall_severity']}",
                'drift_percentage': drift_report['summary']['drift_percentage'],
                'training_result': training_result
            }
        except Exception as e:
            return {
                'triggered': False,
                'error': str(e)
            }
