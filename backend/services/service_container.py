from typing import Dict, Any, Optional
import logging
from .auth_service import AuthService
from .vm_service import VMService
from .project_service import ProjectService
from .billing_service import BillingService
from .monitoring_service import MonitoringService
from .user_service import UserService

class ServiceContainer:
    """Dependency injection container for services"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all services"""
        if self._initialized:
            return
        
        try:
            # Initialize services in dependency order
            self._services["auth"] = AuthService()
            self._services["billing"] = BillingService()
            self._services["user"] = UserService()
            self._services["vm"] = VMService()
            self._services["project"] = ProjectService()
            self._services["monitoring"] = MonitoringService()
            
            self._initialized = True
            self.logger.info("Service container initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize service container: {e}")
            raise
    
    def get_auth_service(self) -> AuthService:
        """Get authentication service"""
        self._ensure_initialized()
        return self._services["auth"]
    
    def get_vm_service(self) -> VMService:
        """Get VM service"""
        self._ensure_initialized()
        return self._services["vm"]
    
    def get_project_service(self) -> ProjectService:
        """Get project service"""
        self._ensure_initialized()
        return self._services["project"]
    
    def get_billing_service(self) -> BillingService:
        """Get billing service"""
        self._ensure_initialized()
        return self._services["billing"]
    
    def get_monitoring_service(self) -> MonitoringService:
        """Get monitoring service"""
        self._ensure_initialized()
        return self._services["monitoring"]
    
    def get_user_service(self) -> UserService:
        """Get user service"""
        self._ensure_initialized()
        return self._services["user"]
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Run health checks on all services"""
        self._ensure_initialized()
        
        health_results = {}
        overall_status = "healthy"
        
        for service_name, service in self._services.items():
            try:
                health_result = await service.health_check()
                health_results[service_name] = health_result
                
                if health_result.get("status") != "healthy":
                    overall_status = "degraded"
                    
            except Exception as e:
                health_results[service_name] = {
                    "service": service_name,
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": health_results,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use datetime.utcnow() in real implementation
        }
    
    def _ensure_initialized(self):
        """Ensure container is initialized"""
        if not self._initialized:
            self.initialize()

# Global service container instance
service_container = ServiceContainer()