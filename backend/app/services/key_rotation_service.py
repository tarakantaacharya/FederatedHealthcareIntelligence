"""
Key rotation service (Phase 20)
Manages cryptographic key lifecycle
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class KeyRotationService:
    """Service for managing key rotation"""
    
    KEY_STORAGE_PATH = "/app/storage/keys"
    KEY_ROTATION_DAYS = 90  # Rotate keys every 90 days
    
    @staticmethod
    def generate_new_key_pair() -> tuple:
        """
        Generate new RSA key pair
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Generate public key
        public_key = private_key.public_key()
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def save_key_pair(
        key_id: str,
        private_key: bytes,
        public_key: bytes,
        metadata: Optional[Dict] = None
    ):
        """
        Save key pair with metadata
        
        Args:
            key_id: Unique key identifier
            private_key: Private key bytes
            public_key: Public key bytes
            metadata: Additional metadata
        """
        os.makedirs(KeyRotationService.KEY_STORAGE_PATH, exist_ok=True)
        
        key_dir = os.path.join(KeyRotationService.KEY_STORAGE_PATH, key_id)
        os.makedirs(key_dir, exist_ok=True)
        
        # Save keys
        with open(os.path.join(key_dir, 'private.pem'), 'wb') as f:
            f.write(private_key)
        
        with open(os.path.join(key_dir, 'public.pem'), 'wb') as f:
            f.write(public_key)
        
        # Save metadata
        metadata = metadata or {}
        metadata['created_at'] = datetime.now().isoformat()
        metadata['expires_at'] = (
            datetime.now() + timedelta(days=KeyRotationService.KEY_ROTATION_DAYS)
        ).isoformat()
        
        with open(os.path.join(key_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def load_current_key(key_id: str) -> tuple:
        """
        Load current key pair
        
        Args:
            key_id: Key identifier
        
        Returns:
            Tuple of (private_key, public_key, metadata)
        """
        key_dir = os.path.join(KeyRotationService.KEY_STORAGE_PATH, key_id)
        
        if not os.path.exists(key_dir):
            raise FileNotFoundError(f"Key {key_id} not found")
        
        # Load keys
        with open(os.path.join(key_dir, 'private.pem'), 'rb') as f:
            private_key = f.read()
        
        with open(os.path.join(key_dir, 'public.pem'), 'rb') as f:
            public_key = f.read()
        
        # Load metadata
        with open(os.path.join(key_dir, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        return private_key, public_key, metadata
    
    @staticmethod
    def rotate_key(key_id: str) -> Dict:
        """
        Rotate key - generate new key and archive old one
        
        Args:
            key_id: Key identifier to rotate
        
        Returns:
            Rotation result dictionary
        """
        # Load old key
        try:
            old_private, old_public, old_metadata = KeyRotationService.load_current_key(key_id)
            
            # Archive old key
            archive_id = f"{key_id}_archived_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            KeyRotationService.save_key_pair(
                archive_id,
                old_private,
                old_public,
                {**old_metadata, 'archived': True}
            )
        except FileNotFoundError:
            old_metadata = {}
        
        # Generate new key
        new_private, new_public = KeyRotationService.generate_new_key_pair()
        
        # Save new key
        KeyRotationService.save_key_pair(
            key_id,
            new_private,
            new_public,
            {
                'rotated_from': old_metadata.get('created_at'),
                'rotation_reason': 'scheduled_rotation'
            }
        )
        
        return {
            'status': 'rotated',
            'key_id': key_id,
            'rotated_at': datetime.now().isoformat(),
            'expires_at': (
                datetime.now() + timedelta(days=KeyRotationService.KEY_ROTATION_DAYS)
            ).isoformat()
        }
    
    @staticmethod
    def check_key_expiry(key_id: str) -> Dict:
        """
        Check if key needs rotation
        
        Args:
            key_id: Key identifier
        
        Returns:
            Expiry status dictionary
        """
        try:
            _, _, metadata = KeyRotationService.load_current_key(key_id)
            
            expires_at = datetime.fromisoformat(metadata['expires_at'])
            days_until_expiry = (expires_at - datetime.now()).days
            
            return {
                'key_id': key_id,
                'expires_at': metadata['expires_at'],
                'days_until_expiry': days_until_expiry,
                'needs_rotation': days_until_expiry <= 7,
                'is_expired': days_until_expiry < 0
            }
        except FileNotFoundError:
            return {
                'key_id': key_id,
                'exists': False,
                'needs_rotation': True,
                'message': 'Key not found - needs initialization'
            }
