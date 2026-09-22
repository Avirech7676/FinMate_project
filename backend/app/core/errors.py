from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class AppException(HTTPException):
    """Base application exception with standardized code and request ID tracking."""
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        err_payload: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.request_id:
            err_payload["request_id"] = self.request_id
        if self.details is not None:
            err_payload["details"] = self.details
        return {"error": err_payload}

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict()
        )

class EntityNotFoundError(AppException):
    def __init__(self, entity: str, identifier: Any, request_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{entity.upper()}_NOT_FOUND",
            message=f"{entity} with ID {identifier} was not found.",
            request_id=request_id
        )

class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None, request_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
            request_id=request_id
        )

class AuthenticationError(AppException):
    def __init__(self, message: str = "Could not validate credentials", request_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            request_id=request_id
        )

class AuthorizationError(AppException):
    def __init__(self, message: str = "Not authorized to access this resource", request_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message,
            request_id=request_id
        )

class ServiceUnavailableError(AppException):
    def __init__(self, service: str, message: Optional[str] = None, request_id: Optional[str] = None):
        msg = message or f"{service} service is temporarily unavailable. Core platform functionality remains operational."
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=f"{service.upper().replace(' ', '_')}_UNAVAILABLE",
            message=msg,
            request_id=request_id
        )
