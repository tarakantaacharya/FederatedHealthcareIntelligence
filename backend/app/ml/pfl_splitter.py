"""
Personalized Federated Learning (PFL) parameter splitter
Separates model parameters into shared (for aggregation) vs local (hospital-private)
"""
import torch
import json
from typing import Dict, Tuple
import numpy as np


class PFLParameterSplitter:
    """Helper for splitting model parameters in PFL mode"""
    
    @staticmethod
    def split_model_parameters(model_weights: Dict, model_type: str) -> Dict[str, Dict]:
        """
        Split model parameters into shared (for aggregation) and local (hospital-private)
        
        Args:
            model_weights: Full model weights dictionary
            model_type: 'ML_REGRESSION' or 'TFT'
        
        Returns:
            {
                "shared": state_dict subset for aggregation,
                "local": state_dict subset to keep at hospital
            }
        """
        if model_type == "ML_REGRESSION":
            return PFLParameterSplitter._split_ml_regression(model_weights)
        elif model_type == "TFT":
            return PFLParameterSplitter._split_tft(model_weights)
        else:
            # Fallback: treat all as shared (FedAvg behavior)
            return {
                "shared": model_weights,
                "local": {}
            }
    
    @staticmethod
    def _split_ml_regression(weights: Dict) -> Dict[str, Dict]:
        """
        Split ML_REGRESSION model parameters
        
        Strategy:
        - Shared: feature transformation, main model weights
        - Local: final output layer bias/weights
        
        For sklearn RandomForest (stored as serialized structure):
        We treat tree structures as shared and keep calibration/scaling as local
        """
        shared = {}
        local = {}
        
        for key, value in weights.items():
            # Keep final layer parameters local
            if any(pattern in key.lower() for pattern in ['bias', 'final', 'output_layer', 'head']):
                local[key] = value
            else:
                # Main model parameters are shared
                shared[key] = value
        
        # If no explicit local parameters found, create minimal local state
        if not local:
            # For sklearn models, keep scaler parameters local
            if 'scaler_mean' in weights or 'scaler_scale' in weights:
                for key in ['scaler_mean', 'scaler_scale', 'scaler_var']:
                    if key in weights:
                        local[key] = weights[key]
                        shared.pop(key, None)
        
        return {"shared": shared, "local": local}
    
    @staticmethod
    def _split_tft(weights: Dict) -> Dict[str, Dict]:
        """
        Split TFT model parameters
        
        Strategy:
        - Shared: encoder, attention blocks, LSTM layers
        - Local: final output projection layer
        """
        shared = {}
        local = {}
        
        for key, value in weights.items():
            # Local head patterns for TFT
            if any(pattern in key.lower() for pattern in [
                'output_projection',
                'final_linear',
                'output_layer',
                'decode_output'
            ]):
                local[key] = value
            else:
                # Encoder, attention, LSTM are shared
                shared[key] = value
        
        # If no explicit local head found, keep last layer as local
        if not local and weights:
            # Take last 1-2 weight keys as local fallback
            keys = list(weights.keys())
            if len(keys) > 2:
                last_keys = keys[-2:]
                for key in last_keys:
                    local[key] = weights[key]
                    shared.pop(key, None)
        
        return {"shared": shared, "local": local}
    
    @staticmethod
    def merge_shared_with_local(
        new_shared_weights: Dict,
        local_head_weights: Dict
    ) -> Dict:
        """
        Merge updated shared weights with local head after aggregation
        
        Args:
            new_shared_weights: Aggregated shared parameters from central
            local_head_weights: Hospital's private local head
        
        Returns:
            Complete model with merged shared+local parameters
        """
        merged = {}
        merged.update(new_shared_weights)
        merged.update(local_head_weights)
        return merged
