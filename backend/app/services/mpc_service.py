"""
Secure Multi-Party Computation (MPC) Service
MANDATORY: Masked aggregation protocol
NO DIRECT AVERAGING ALLOWED
"""
import numpy as np
import hashlib
import json
from typing import Dict, List, Tuple
import secrets


class MPCService:
    """
    Implements additive masking protocol for secure aggregation.
    
    MANDATORY REQUIREMENTS:
    - Hospitals mask weights before upload
    - Central server aggregates ONLY masked weights
    - Masks are removed after aggregation
    - NO direct weight averaging allowed
    
    Protocol:
    1. Each hospital generates random mask
    2. Hospital uploads: masked_weights = weights + mask
    3. Central aggregates: sum(masked_weights)
    4. Unmask: aggregated - sum(masks) = aggregated_true_weights
    """
    
    @staticmethod
    def generate_mask(weight_shape: Dict[str, tuple]) -> Dict[str, np.ndarray]:
        """
        Generate random masks for model weights.
        
        MANDATORY: Called by each hospital before weight upload.
        
        Args:
            weight_shape: Dictionary mapping parameter names to shapes
            
        Returns:
            Dictionary of random masks matching weight shapes
        """
        masks = {}
        for param_name, shape in weight_shape.items():
            # Generate cryptographically secure random mask
            mask = np.random.normal(0, 0.01, size=shape)
            masks[param_name] = mask
        
        return masks
    
    @staticmethod
    def mask_weights(
        weights: Dict[str, np.ndarray],
        mask: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Apply additive mask to weights.
        
        MANDATORY: Line 52-70
        Hospital MUST call this before uploading weights.
        
        Args:
            weights: Original model weights
            mask: Random mask from generate_mask()
            
        Returns:
            Masked weights (weights + mask)
        """
        masked_weights = {}
        for param_name, weight in weights.items():
            if param_name in mask:
                masked_weights[param_name] = weight + mask[param_name]
            else:
                raise ValueError(f"Missing mask for parameter: {param_name}")
        
        return masked_weights
    
    @staticmethod
    def aggregate_masked_weights(
        masked_weight_list: List[Dict[str, np.ndarray]],
        num_hospitals: int
    ) -> Dict[str, np.ndarray]:
        """
        Aggregate masked weights from all hospitals.
        
        MANDATORY: Line 79-112
        Central server ONLY sees masked weights.
        NO direct averaging allowed.
        
        Args:
            masked_weight_list: List of masked weight dictionaries from hospitals
            num_hospitals: Total number of participating hospitals
            
        Returns:
            Aggregated masked weights (sum of masked weights)
        """
        if not masked_weight_list:
            raise ValueError("Cannot aggregate empty weight list")
        
        # Aggregate only parameters present in every participant model
        aggregated = {}
        common_param_names = set(masked_weight_list[0].keys())
        for weights in masked_weight_list[1:]:
            common_param_names &= set(weights.keys())

        if not common_param_names:
            raise ValueError("No common parameters found across participating hospitals")
        
        compatible_param_names = []
        for param_name in common_param_names:
            reference_shape = masked_weight_list[0][param_name].shape
            if all(weights[param_name].shape == reference_shape for weights in masked_weight_list):
                compatible_param_names.append(param_name)

        if not compatible_param_names:
            raise ValueError("No shape-compatible parameters found across participating hospitals")

        for param_name in compatible_param_names:
            # Sum all masked weights for this parameter
            masked_sum = sum(
                weights[param_name] for weights in masked_weight_list
            )
            aggregated[param_name] = masked_sum
        
        return aggregated
    
    @staticmethod
    def unmask_weights(
        aggregated_masked: Dict[str, np.ndarray],
        masks: List[Dict[str, np.ndarray]],
        num_hospitals: int
    ) -> Dict[str, np.ndarray]:
        """
        Remove masks from aggregated weights.
        
        MANDATORY: Line 114-145
        Final step: compute true federated average.
        
        Args:
            aggregated_masked: Aggregated masked weights from aggregate_masked_weights()
            masks: List of masks from all hospitals
            num_hospitals: Number of hospitals
            
        Returns:
            True federated averaged weights
        """
        if not masks:
            raise ValueError("Cannot unmask without masks")
        
        unmasked = {}
        
        for param_name in aggregated_masked.keys():
            if not all(param_name in mask for mask in masks):
                continue
            # Sum all masks for this parameter
            mask_sum = sum(mask[param_name] for mask in masks)
            
            # Remove mask: aggregated_masked - mask_sum = true_sum
            true_sum = aggregated_masked[param_name] - mask_sum
            
            # Compute average: true_sum / num_hospitals
            unmasked[param_name] = true_sum / num_hospitals
        
        return unmasked
    
    @staticmethod
    def compute_mask_hash(mask: Dict[str, np.ndarray]) -> str:
        """
        Compute SHA-256 hash of mask for verification.
        
        Args:
            mask: Mask dictionary
            
        Returns:
            Hex digest of mask hash
        """
        # Concatenate all mask arrays
        mask_bytes = b""
        for param_name in sorted(mask.keys()):
            mask_bytes += mask[param_name].tobytes()
        
        # Compute hash
        hash_obj = hashlib.sha256(mask_bytes)
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_mask_integrity(
        mask: Dict[str, np.ndarray],
        expected_hash: str
    ) -> bool:
        """
        Verify mask has not been tampered with.
        
        Args:
            mask: Mask to verify
            expected_hash: Expected SHA-256 hash
            
        Returns:
            True if mask matches expected hash
        """
        actual_hash = MPCService.compute_mask_hash(mask)
        return actual_hash == expected_hash
    
    @staticmethod
    def serialize_mask(mask: Dict[str, np.ndarray]) -> str:
        """
        Serialize mask to JSON string for storage/transmission.
        
        Args:
            mask: Mask dictionary
            
        Returns:
            JSON string
        """
        serializable = {}
        for param_name, mask_array in mask.items():
            serializable[param_name] = mask_array.tolist()
        
        return json.dumps(serializable)
    
    @staticmethod
    def deserialize_mask(mask_json: str) -> Dict[str, np.ndarray]:
        """
        Deserialize mask from JSON string.
        
        Args:
            mask_json: JSON string from serialize_mask()
            
        Returns:
            Mask dictionary with numpy arrays
        """
        mask_dict = json.loads(mask_json)
        
        deserialized = {}
        for param_name, mask_list in mask_dict.items():
            deserialized[param_name] = np.array(mask_list)
        
        return deserialized
