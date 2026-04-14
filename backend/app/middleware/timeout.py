"""
Request timeout middleware — prevents hanging requests from exhausting resources.
Different endpoints have different timeout limits.
"""

import asyncio
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Timeout config by endpoint pattern
TIMEOUT_CONFIG = {
    "/api/v1/transactions/batch": 120,  # 2 min for bulk uploads
    "/api/v1/ml-training": 600,  # 10 min for model training
    "/api/v1/": 30,  # 30 sec default for most endpoints
}


async def timeout_middleware(request: Request, call_next):
    """Enforce timeout on all requests."""

    # Determine timeout based on path
    timeout = 30  # Default 30 seconds
    for pattern, timeout_secs in TIMEOUT_CONFIG.items():
        if request.url.path.startswith(pattern):
            timeout = timeout_secs
            break

    try:
        # Wrap the request with timeout
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        return response
    except asyncio.TimeoutError:
        logger.warning(
            "Request timeout",
            extra={
                "method": request.method,
                "path": request.url.path,
                "timeout_seconds": timeout,
            },
        )
        return JSONResponse(
            status_code=504,
            content={
                "detail": "Request timeout",
                "message": f"Request exceeded {timeout}s timeout limit",
            },
        )
    except Exception as exc:
        # Let other exceptions be handled by error handler
        raise exc
