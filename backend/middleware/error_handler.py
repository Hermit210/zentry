"""
Comprehensive error handling middleware for Zentry Cloud API
Provides consistent error responses and proper HTTP status codes
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from services.base_service import ServiceError, ValidationError, NotFoundError, InsufficientCreditsError
from datetime import datetime
import logging
import traceback
from config import settings

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the API"""
    
    @staticmethod
    def create_error_response(
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict = None,
        request: Request = None
    ) -> JSONResponse:
        """Create a standardized error response"""
        error_response = {
            "success": False,
            "error_code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if details:
            error_response["details"] = details
        
        if request:
            error_response["path"] = str(request.url.path)
            error_response["method"] = request.method
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @staticmethod
    async def service_error_handler(request: Request, exc: ServiceError):
        """Handle service layer errors with appropriate HTTP status codes"""
        # Map service errors to HTTP status codes
        status_code_mapping = {
            "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
            "NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "INSUFFICIENT_CREDITS": status.HTTP_400_BAD_REQUEST,
            "PERMISSION_DENIED": status.HTTP_403_FORBIDDEN,
            "RATE_LIMITED": status.HTTP_429_TOO_MANY_REQUESTS,
            "ACCOUNT_DEACTIVATED": status.HTTP_403_FORBIDDEN,
            "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        status_code = status_code_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log error with appropriate level
        if status_code >= 500:
            logger.error(f"Service error {exc.error_code} on {request.method} {request.url.path}: {exc.message}")
        else:
            logger.warning(f"Service error {exc.error_code} on {request.method} {request.url.path}: {exc.message}")
        
        return ErrorHandler.create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status_code,
            details=exc.details,
            request=request
        )
    
    @staticmethod
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle validation errors from service layer"""
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.message}")
        
        return ErrorHandler.create_error_response(
            error_code="VALIDATION_ERROR",
            message=exc.message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=exc.details,
            request=request
        )
    
    @staticmethod
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        """Handle not found errors from service layer"""
        logger.warning(f"Not found error on {request.method} {request.url.path}: {exc.message}")
        
        return ErrorHandler.create_error_response(
            error_code="NOT_FOUND",
            message=exc.message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=exc.details,
            request=request
        )
    
    @staticmethod
    async def insufficient_credits_error_handler(request: Request, exc: InsufficientCreditsError):
        """Handle insufficient credits errors from service layer"""
        logger.warning(f"Insufficient credits error on {request.method} {request.url.path}: {exc.message}")
        
        return ErrorHandler.create_error_response(
            error_code="INSUFFICIENT_CREDITS",
            message=exc.message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=exc.details,
            request=request
        )
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent format"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
        
        error_code_map = {
            400: "VALIDATION_ERROR",
            401: "AUTHENTICATION_ERROR", 
            403: "AUTHORIZATION_ERROR",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR"
        }
        
        error_code = error_code_map.get(exc.status_code, "UNKNOWN_ERROR")
        
        return ErrorHandler.create_error_response(
            error_code=error_code,
            message=exc.detail,
            status_code=exc.status_code
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed information"""
        logger.warning(f"Validation error: {exc.errors()} - {request.url}")
        
        # Format validation errors for better user experience
        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return ErrorHandler.create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": error_details}
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unhandled exception: {exc} - {request.url}")
        logger.error(traceback.format_exc())
        
        # Don't expose internal errors in production
        if settings.is_production:
            message = "An unexpected error occurred"
            details = None
        else:
            message = str(exc)
            details = {"traceback": traceback.format_exc()}
        
        return ErrorHandler.create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

# Exception handlers for FastAPI app
exception_handlers = {
    ServiceError: ErrorHandler.service_error_handler,
    ValidationError: ErrorHandler.validation_error_handler,
    NotFoundError: ErrorHandler.not_found_error_handler,
    InsufficientCreditsError: ErrorHandler.insufficient_credits_error_handler,
    HTTPException: ErrorHandler.http_exception_handler,
    StarletteHTTPException: ErrorHandler.http_exception_handler,
    RequestValidationError: ErrorHandler.validation_exception_handler,
    Exception: ErrorHandler.general_exception_handler
}