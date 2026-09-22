import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.errors import AppException

logger = logging.getLogger("finmate.access")

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID injection, latency logging, security headers, and safe error handling."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"status={response.status_code} duration={process_time:.4f}s"
            )
            return response
        except AppException as app_err:
            app_err.request_id = request_id
            return app_err.to_response()
        except Exception as exc:
            logger.exception(f"[{request_id}] Unhandled error: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected server error occurred. Please try again later.",
                        "request_id": request_id
                    }
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                }
            )
