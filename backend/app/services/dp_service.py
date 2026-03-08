"""Pure Differential Privacy Service (Refactored)
Implements mathematical DP mechanisms without governance logic

GOVERNANCE SEPARATION:
- NO budget tracking (handled by PrivacyBudgetService)
- NO epsilon decay (handled by PrivacyPolicy)
- NO database access (handled by calling service)
- NO round awareness (parameters passed explicitly)
"""
import numpy as np
from typing import Dict, Tuple


class DifferentialPrivacyService:
    """
    Pure DP mechanism service
    
    Implements:
    - Global gradient/weight clipping
    - Gaussian noise addition
    - Privacy parameter validation
    
    Does NOT implement:
    - Budget tracking
    - Epsilon decay
    - Database operations
    - History tracking
    """
    
    def __init__(self):
        """
        Initialize pure DP service (stateless)
        """
        pass
    

    
    def clip_gradients(
        self,
        gradients: Dict[str, np.ndarray],
        clip_norm: float
    ) -> Dict[str, np.ndarray]:
        """
        Clip gradients using GLOBAL clipping (strict sensitivity bound)
        
        Args:
            gradients: Dictionary of layer gradients/weights
            clip_norm: L2 norm clipping threshold
        
        Returns:
            Clipped gradients with global norm <= clip_norm
        """
        clipped_gradients = {}
        
        # ALWAYS use global clipping for governance compliance
        global_norm = np.sqrt(sum(np.linalg.norm(grad)**2 for grad in gradients.values()))
        
        if global_norm > clip_norm:
            scaling_factor = clip_norm / global_norm
            for layer_name, grad in gradients.items():
                clipped_gradients[layer_name] = grad * scaling_factor
        else:
            clipped_gradients = gradients.copy()
        
        return clipped_gradients
    
    def add_gaussian_noise(
        self,
        gradients: Dict[str, np.ndarray],
        epsilon: float,
        delta: float,
        clip_norm: float,
        noise_multiplier: float
    ) -> Tuple[Dict[str, np.ndarray], float]:
        """
        Add calibrated Gaussian noise to gradients/weights
        
        Args:
            gradients: Clipped gradients/weights
            epsilon: Privacy budget
            delta: Privacy parameter
            clip_norm: Sensitivity bound (from clipping)
            noise_multiplier: Noise scale multiplier
        
        Returns:
            Tuple of (noisy_gradients, noise_scale)
        """
        # Calculate noise scale using Gaussian mechanism
        # σ = (sensitivity * √(2 * ln(1.25/δ))) / ε
        noise_scale = (clip_norm * np.sqrt(2 * np.log(1.25 / delta))) / epsilon
        noise_scale *= noise_multiplier
        
        noisy_gradients = {}
        
        for layer_name, grad in gradients.items():
            noise = np.random.normal(0, noise_scale, grad.shape)
            noisy_gradients[layer_name] = grad + noise
        
        return noisy_gradients, noise_scale
    
    def apply_dp_to_weights(
        self,
        weights: Dict[str, np.ndarray],
        epsilon: float,
        delta: float,
        clip_norm: float,
        noise_multiplier: float
    ) -> Tuple[Dict[str, np.ndarray], Dict]:
        """
        Apply pure DP mechanism to model weights (NO governance logic)
        
        Args:
            weights: Model weights dictionary
            epsilon: Privacy budget (from policy)
            delta: Privacy parameter (from policy)
            clip_norm: L2 clipping threshold (from policy)
            noise_multiplier: Noise scale multiplier (from policy)
        
        Returns:
            Tuple of (privatized_weights, privacy_metadata)
        
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if delta <= 0 or delta >= 1:
            raise ValueError(f"Delta must be in (0, 1), got {delta}")
        if clip_norm <= 0:
            raise ValueError(f"Clip norm must be positive, got {clip_norm}")
        if noise_multiplier < 0:
            raise ValueError(f"Noise multiplier must be non-negative, got {noise_multiplier}")
        
        # Step 1: Clip weights (GLOBAL clipping for strict sensitivity)
        clipped_weights = self.clip_gradients(weights, clip_norm)
        
        # Step 2: Add calibrated Gaussian noise
        private_weights, noise_scale = self.add_gaussian_noise(
            clipped_weights,
            epsilon,
            delta,
            clip_norm,
            noise_multiplier
        )
        
        # Step 3: Return weights and metadata (NO database writes, NO budget tracking)
        privacy_metadata = {
            "epsilon": float(epsilon),
            "delta": float(delta),
            "clip_norm": float(clip_norm),
            "noise_multiplier": float(noise_multiplier),
            "noise_scale": float(noise_scale),
            "mechanism": "gaussian_weight_perturbation"
        }
        
        return private_weights, privacy_metadata
    

