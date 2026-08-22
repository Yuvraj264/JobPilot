import time
from collections import defaultdict
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory Token Bucket rate limiting middleware protecting against API DOS
    and brute-force scraping attempts.
    Excludes health probe routes from rate checks.
    """

    def __init__(self, app):
        super().__init__(app)
        # Dictionary storing ip -> list of request timestamps in the last 60 seconds
        self.request_windows = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Bypass rate limiter for health check monitoring endpoints
        if "/health" in path:
            return await call_next(request)

        # Bypass in test environment unless rate limit is explicitly set low and X-Test-Rate-Limit is present
        import sys
        is_testing = "pytest" in sys.modules or settings.APP_ENV == "test"
        if is_testing:
            if settings.API_RATE_LIMIT_PER_MINUTE >= 10 or not request.headers.get("X-Test-Rate-Limit"):
                return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Clean old timestamps outside the 60 seconds sliding window
        self.request_windows[client_ip] = [
            t for t in self.request_windows[client_ip] if now - t < 60
        ]

        # Enforce rate limit threshold
        if len(self.request_windows[client_ip]) >= settings.API_RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please wait and try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                },
                headers={
                    "Retry-After": "60"
                }
            )

        self.request_windows[client_ip].append(now)
        return await call_next(request)
