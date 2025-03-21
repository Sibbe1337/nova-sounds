"""
Error handling utilities for the YouTube Shorts Machine application.
"""
from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.app.core.logging import get_logger, log_exception

# Set up logger
logger = get_logger(__name__)

# Error response model
class ErrorResponse(BaseModel):
    """Standardized error response model."""
    status: int
    detail: str
    code: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None

# Custom application exceptions
class ApplicationError(Exception):
    """Base class for application-specific errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.errors = errors
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """Validation error for invalid input data."""
    def __init__(
        self, 
        message: str = "Validation error", 
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            errors=errors
        )

class ResourceNotFoundError(ApplicationError):
    """Error for resource not found."""
    def __init__(
        self, 
        resource_type: str, 
        resource_id: Union[str, int]
    ):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND"
        )

class AuthenticationError(ApplicationError):
    """Error for authentication issues."""
    def __init__(
        self, 
        message: str = "Authentication failed"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(ApplicationError):
    """Error for authorization issues."""
    def __init__(
        self, 
        message: str = "Not authorized to perform this action"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )

class ServiceUnavailableError(ApplicationError):
    """Error for external service unavailability."""
    def __init__(
        self, 
        service: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Service {service} is currently unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE"
        )

# Exception handler function for FastAPI
async def application_exception_handler(request, exc: ApplicationError) -> JSONResponse:
    """
    Handle ApplicationError exceptions and return standardized response.
    """
    # Log the error
    logger.error(f"{exc.error_code}: {exc.message}")
    
    # Create error response
    response = ErrorResponse(
        status=exc.status_code,
        detail=exc.message,
        code=exc.error_code,
        errors=exc.errors
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict(exclude_none=True)
    )

# Helper functions for standard error responses
def not_found_response(resource_type: str, resource_id: Union[str, int]) -> JSONResponse:
    """Generate a standardized 404 response."""
    error = ResourceNotFoundError(resource_type, resource_id)
    
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            status=error.status_code,
            detail=error.message,
            code=error.error_code
        ).dict(exclude_none=True)
    )

def validation_error_response(errors: List[Dict[str, Any]]) -> JSONResponse:
    """Generate a standardized validation error response."""
    error = ValidationError(errors=errors)
    
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            status=error.status_code,
            detail=error.message,
            code=error.error_code,
            errors=errors
        ).dict(exclude_none=True)
    )

def auth_error_response(message: str = "Authentication required") -> JSONResponse:
    """Generate a standardized authentication error response."""
    error = AuthenticationError(message)
    
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            status=error.status_code,
            detail=error.message,
            code=error.error_code
        ).dict(exclude_none=True)
    )

def service_error_response(service: str, message: Optional[str] = None) -> JSONResponse:
    """Generate a standardized service unavailable response."""
    error = ServiceUnavailableError(service, message)
    
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            status=error.status_code,
            detail=error.message,
            code=error.error_code
        ).dict(exclude_none=True)
    ) 