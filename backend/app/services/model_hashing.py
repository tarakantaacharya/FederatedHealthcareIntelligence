"""
Model hashing service (Phase 19)
Cryptographic hashing for model integrity
"""
import hashlib
import json
from typing import Dict


class ModelHashingService:
    """Service for hashing and verifying models"""
    
    @staticmethod
    def hash_model_file(model_path: str) -> str:
        """
        Generate SHA-256 hash of model file
        
        Args:
            model_path: Path to model file
        
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        
        with open(model_path, 'rb') as f:
            # Read file in chunks to handle large models
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    @staticmethod
    def hash_model_weights(weights: Dict) -> str:
        """
        Generate hash of model weights dictionary
        
        Args:
            weights: Model weights dictionary
        
        Returns:
            Hexadecimal hash string
        """
        # Convert to deterministic JSON string
        weights_json = json.dumps(weights, sort_keys=True)
        
        sha256 = hashlib.sha256()
        sha256.update(weights_json.encode('utf-8'))
        
        return sha256.hexdigest()
    
    @staticmethod
    def verify_model_hash(model_path: str, expected_hash: str) -> bool:
        """
        Verify model file against expected hash
        
        Args:
            model_path: Path to model file
            expected_hash: Expected hash value
        
        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = ModelHashingService.hash_model_file(model_path)
        return actual_hash == expected_hash
    
    @staticmethod
    def verify_weights_hash(weights: Dict, expected_hash: str) -> bool:
        """
        Verify model weights against expected hash
        
        Args:
            weights: Model weights dictionary
            expected_hash: Expected hash value
        
        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = ModelHashingService.hash_model_weights(weights)
        return actual_hash == expected_hash
    
    @staticmethod
    def generate_merkle_root(hashes: list) -> str:
        """
        Generate Merkle root from list of hashes
        
        Useful for verifying multiple models/weights
        
        Args:
            hashes: List of hash strings
        
        Returns:
            Merkle root hash
        """
        if not hashes:
            return ""
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Build Merkle tree
        current_level = hashes[:]
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                
                sha256 = hashlib.sha256()
                sha256.update(combined.encode('utf-8'))
                next_level.append(sha256.hexdigest())
            
            current_level = next_level
        
        return current_level[0]
