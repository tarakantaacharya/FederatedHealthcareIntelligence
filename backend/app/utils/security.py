"""
Security utilities for password hashing and JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Bcrypt hash (always 60 characters for bcrypt)
    
    Raises:
        ValueError: If hash generation fails or produces invalid output
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    
    hashed = pwd_context.hash(password)
    
    # Validate bcrypt hash is correct length (always 60 chars: $2b$12$...)
    if len(hashed) != 60:
        raise ValueError(
            f"Password hash validation failed: expected 60 characters, got {len(hashed)}. "
            f"This indicates a bcrypt generation error."
        )
    
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored bcrypt hash
    
    Returns:
        True if password matches, False otherwise
    
    Raises:
        ValueError: If hash is corrupted or invalid format
    """
    if not plain_password or not isinstance(plain_password, str):
        return False
    
    if not hashed_password or not isinstance(hashed_password, str):
        raise ValueError("Stored password hash is invalid or missing")
    
    # Validate hash is proper bcrypt format and length
    if not hashed_password.startswith("$2a$") and not hashed_password.startswith("$2b$") and not hashed_password.startswith("$2y$"):
        raise ValueError(
            f"Password hash validation failed: hash does not start with bcrypt identifier. "
            f"Expected to start with '$2a$', '$2b$', or '$2y$', got '{hashed_password[:10]}'... "
            f"Hash may be corrupted or truncated (length: {len(hashed_password)})."
        )
    
    if len(hashed_password) != 60:
        raise ValueError(
            f"Password hash validation failed: expected 60 characters, got {len(hashed_password)}. "
            f"Hash is corrupted or truncated. First 20 chars: {hashed_password[:20]}"
        )
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise ValueError(f"Password verification failed: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for hospitals using SECRET_KEY
    """
    to_encode = data.copy()

    if "role" not in to_encode:
        to_encode["role"] = "HOSPITAL"

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_admin_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for admins using ADMIN_SECRET_KEY
    """
    to_encode = data.copy()

    if "role" not in to_encode:
        to_encode["role"] = "ADMIN"

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.ADMIN_SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
