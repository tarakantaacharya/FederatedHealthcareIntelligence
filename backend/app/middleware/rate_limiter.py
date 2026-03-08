"""
Rate Limiting Middleware (Phase 39)
Prevents abuse and DDoS attacks
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware
    
    Limits:
    - 100 requests per minute per IP (general)
    - 10 login attempts per minute per IP
    - 20 training requests per hour per hospital
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Store: {ip: (tokens, last_refill_time)}
        self.general_buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (100, time.time()))
        
        # Store: {ip: (tokens, last_refill_time)}
        self.login_buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (10, time.time()))
        
        # Store: {hospital_id: (tokens, last_refill_time)}
        self.training_buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (20, time.time()))
        
        # Configuration
        self.general_limit = 100  # requests per minute
        self.general_refill_rate = 100 / 60  # tokens per second
        
        self.login_limit = 10  # requests per minute
        self.login_refill_rate = 10 / 60
        
        self.training_limit = 20  # requests per hour
        self.training_refill_rate = 20 / 3600
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Get client IP
        client_ip = request.client.host
        path = request.url.path
        
        # Check rate limits based on endpoint
        try:
            if '/api/auth/login' in path:
                self._check_login_limit(client_ip)
            elif '/api/training/' in path:
                hospital_id = self._get_hospital_id_from_request(request)
                if hospital_id:
                    self._check_training_limit(hospital_id)
            else:
                self._check_general_limit(client_ip)
        
        except HTTPException as e:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(self.general_limit)
        response.headers['X-RateLimit-Remaining'] = str(self._get_remaining_tokens(client_ip))
        
        return response
    
    def _check_general_limit(self, client_ip: str):
        """Check general rate limit"""
        if not self._consume_token(
            self.general_buckets,
            client_ip,
            self.general_limit,
            self.general_refill_rate
        ):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
    
    def _check_login_limit(self, client_ip: str):
        """Check login rate limit"""
        if not self._consume_token(
            self.login_buckets,
            client_ip,
            self.login_limit,
            self.login_refill_rate
        ):
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again in 1 minute."
            )
    
    def _check_training_limit(self, hospital_id: str):
        """Check training rate limit"""
        if not self._consume_token(
            self.training_buckets,
            hospital_id,
            self.training_limit,
            self.training_refill_rate
        ):
            raise HTTPException(
                status_code=429,
                detail="Training rate limit exceeded. Maximum 20 requests per hour."
            )
    
    def _consume_token(
        self,
        buckets: Dict[str, Tuple[int, float]],
        key: str,
        limit: int,
        refill_rate: float
    ) -> bool:
        """
        Token bucket algorithm implementation
        
        Returns True if token available, False otherwise
        """
        current_time = time.time()
        tokens, last_refill = buckets[key]
        
        # Refill tokens based on time elapsed
        time_passed = current_time - last_refill
        tokens += time_passed * refill_rate
        tokens = min(tokens, limit)  # Cap at limit
        
        # Try to consume token
        if tokens >= 1:
            tokens -= 1
            buckets[key] = (tokens, current_time)
            return True
        else:
            buckets[key] = (tokens, current_time)
            return False
    
    def _get_remaining_tokens(self, client_ip: str) -> int:
        """Get remaining tokens for IP"""
        if client_ip in self.general_buckets:
            tokens, _ = self.general_buckets[client_ip]
            return int(tokens)
        return self.general_limit
    
    def _get_hospital_id_from_request(self, request: Request) -> str:
        """Extract hospital ID from JWT token"""
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                from app.utils.security import decode_token
                payload = decode_token(token)
                return payload.get('sub')
        except Exception:
            pass
        
        return None
