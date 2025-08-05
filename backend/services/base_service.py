from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging
from database import db, DatabaseError
from models import APIResponse, ErrorResponse
import uuid

class ServiceError(Exception):
    """Base service error"""
    def __init__(self, message: str, error_code: str = "SERVICE_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ServiceError):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundError(ServiceError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} not found: {identifier}", "NOT_FOUND", {"resource": resource, "id": identifier})

class InsufficientCreditsError(ServiceError):
    """Insufficient credits error"""
    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient credits. Required: ${required:.2f}, Available: ${available:.2f}",
            "INSUFFICIENT_CREDITS",
            {"required": required, "available": available}
        )

class BaseService(ABC):
    """Base service class with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
    
    def generate_id(self) -> str:
        """Generate a unique UUID"""
        return str(uuid.uuid4())
    
    def create_success_response(self, message: str, data: Optional[Dict[str, Any]] = None) -> APIResponse:
        """Create a success API response"""
        return APIResponse(
            success=True,
            message=message,
            data=data,
            timestamp=datetime.utcnow()
        )
    
    def create_error_response(self, error: ServiceError) -> ErrorResponse:
        """Create an error response from a service error"""
        return ErrorResponse(
            success=False,
            error_code=error.error_code,
            message=error.message,
            details=error.details,
            timestamp=datetime.utcnow()
        )
    
    async def log_audit_event(self, user_id: str, action: str, resource_type: str, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log an audit event"""
        try:
            audit_record = {
                "id": self.generate_id(),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self.db.get_client():
                # Supabase implementation
                supabase = self.db.get_client()
                supabase.table("audit_logs").insert(audit_record).execute()
            else:
                # In-memory implementation
                memory_store = self.db.get_memory_store()
                memory_store["audit_logs"].append(audit_record)
                
        except Exception as e:
            self.logger.warning(f"Failed to log audit event: {e}")
    
    async def validate_user_ownership(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Validate that a user owns a specific resource"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table(resource_type).select("user_id").eq("id", resource_id).execute()
                if result.data and result.data[0]["user_id"] == user_id:
                    return True
            else:
                # In-memory validation
                memory_store = self.db.get_memory_store()
                resources = memory_store.get(resource_type, [])
                for resource in resources:
                    if resource.get("id") == resource_id and resource.get("user_id") == user_id:
                        return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error validating user ownership: {e}")
            return False
    
    def handle_database_error(self, e: Exception, operation: str) -> ServiceError:
        """Convert database errors to service errors"""
        self.logger.error(f"Database error during {operation}: {e}")
        
        if isinstance(e, DatabaseError):
            return ServiceError(f"Database error during {operation}", "DATABASE_ERROR", {"operation": operation})
        
        return ServiceError(f"Internal error during {operation}", "INTERNAL_ERROR", {"operation": operation})
    
    async def get_user_credits(self, user_id: str) -> float:
        """Get current user credits"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").select("credits").eq("id", user_id).execute()
                if result.data:
                    return float(result.data[0]["credits"])
            else:
                memory_store = self.db.get_memory_store()
                for user_data in memory_store["users"].values():
                    if user_data.get("id") == user_id:
                        return float(user_data.get("credits", 0.0))
            
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting user credits: {e}")
            return 0.0
    
    async def update_user_credits(self, user_id: str, new_credits: float) -> bool:
        """Update user credits"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
                return bool(result.data)
            else:
                memory_store = self.db.get_memory_store()
                for user_data in memory_store["users"].values():
                    if user_data.get("id") == user_id:
                        user_data["credits"] = new_credits
                        return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error updating user credits: {e}")
            return False
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Service-specific health check"""
        pass