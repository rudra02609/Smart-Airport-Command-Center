"""
Security middleware for the Smart Airport Command Center.
Includes rate limiting and security headers.

The rate limiting uses an in-memory store, which is appropriate for
development and single-process deployments. For production scale-out,
replace with a shared store (e.g. Redis) as documented.
"""

import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.cybersecurity.anomaly_detection import anomaly_detector


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Limits requests per IP within a configurable time window.
    Every request (including rejected ones) is also recorded in the
    anomaly detector so that global request patterns are observable.
    """
    
    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW
        # Track request timestamps per IP
        self.request_log: dict[str, list[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Record every request for anomaly detection analysis.
        # The anomaly detector prunes old entries internally.
        anomaly_detector.record_request(client_ip, request.url.path)
        
        # Clean old entries outside the window
        cutoff = now - self.window_seconds
        self.request_log[client_ip] = [
            t for t in self.request_log[client_ip] if t > cutoff
        ]
        
        # Check rate limit
        if len(self.request_log[client_ip]) >= self.max_requests:
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json"
            )
        
        # Record this request
        self.request_log[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security-related HTTP headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        
        return response
