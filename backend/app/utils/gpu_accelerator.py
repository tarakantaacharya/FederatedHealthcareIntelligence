"""
GPU Acceleration Support (Phase 36)
Optional GPU paths with graceful CPU fallback
"""
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Check GPU availability
GPU_AVAILABLE = False
DEVICE = "cpu"

try:
    import torch
    if torch.cuda.is_available():
        GPU_AVAILABLE = True
        DEVICE = "cuda"
        logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA version: {torch.version.cuda}")
    else:
        logger.info("PyTorch available but no CUDA GPU detected. Using CPU.")
except ImportError:
    logger.info("PyTorch not installed. GPU acceleration unavailable.")


class GPUAccelerator:
    """GPU acceleration utilities"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if GPU is available"""
        return GPU_AVAILABLE
    
    @staticmethod
    def get_device() -> str:
        """Get device string ('cuda' or 'cpu')"""
        return DEVICE
    
    @staticmethod
    def get_device_info() -> Dict:
        """Get detailed device information"""
        info = {
            'gpu_available': GPU_AVAILABLE,
            'device': DEVICE,
            'backend': 'pytorch' if GPU_AVAILABLE else 'cpu'
        }
        
        if GPU_AVAILABLE:
            try:
                import torch
                info['gpu_name'] = torch.cuda.get_device_name(0)
                info['cuda_version'] = torch.version.cuda
                info['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB
                info['gpu_memory_available'] = (torch.cuda.get_device_properties(0).total_memory - 
                                                 torch.cuda.memory_allocated(0)) / 1e9
            except Exception as e:
                logger.error(f"Error getting GPU info: {e}")
        
        return info
    
    @staticmethod
    def to_device(model, device: Optional[str] = None):
        """
        Move model to specified device
        
        Args:
            model: PyTorch model
            device: Target device ('cuda' or 'cpu'), auto-detect if None
        
        Returns:
            Model on target device
        """
        if device is None:
            device = DEVICE
        
        try:
            import torch
            if isinstance(model, torch.nn.Module):
                model = model.to(device)
                logger.info(f"Model moved to {device}")
        except Exception as e:
            logger.warning(f"Could not move model to {device}: {e}")
        
        return model
    
    @staticmethod
    def optimize_memory():
        """Clear GPU cache if available"""
        if GPU_AVAILABLE:
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared")
            except Exception as e:
                logger.error(f"Error clearing GPU cache: {e}")
    
    @staticmethod
    def get_optimal_batch_size(model_size_mb: float = 100) -> int:
        """
        Get optimal batch size based on available memory
        
        Args:
            model_size_mb: Estimated model size in MB
        
        Returns:
            Recommended batch size
        """
        if GPU_AVAILABLE:
            try:
                import torch
                gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                
                # Reserve 20% for overhead
                available_gb = gpu_mem_gb * 0.8
                model_size_gb = model_size_mb / 1000
                
                # Rough estimate: batch_size = available_memory / (model_size * 10)
                batch_size = int(available_gb / (model_size_gb * 10))
                batch_size = max(8, min(batch_size, 512))  # Clamp between 8-512
                
                logger.info(f"Recommended batch size for GPU: {batch_size}")
                return batch_size
            except Exception as e:
                logger.error(f"Error calculating batch size: {e}")
        
        # CPU fallback
        return 32
