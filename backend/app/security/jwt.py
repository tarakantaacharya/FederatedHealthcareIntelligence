"""
JWT utilities for WebSocket authentication (Phase 27)
"""
from fastapi import WebSocketException, status
from jose import jwt, JWTError
from app.config import get_settings

settings = get_settings()


def verify_ws_token(token: str) -> dict:
    """
    Verify JWT token for WebSocket connections
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        WebSocketException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
