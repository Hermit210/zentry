"""
Health check endpoints for monitoring database and system status
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging
from database_service import database_service
from auth import get_current_user
from models import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    try:
        health_status = await database_service.health_check()
        
        return {
            "status": "healthy" if health_status["status"] == "healthy" else "unhealthy",
            "timestamp": health_status.get("last_check"),
            "database": health_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/database", response_model=Dict[str, Any])
async def database_health():
    """Detailed database health check"""
    try:
        return await database_service.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database health check failed")

@router.get("/database/statistics", response_model=Dict[str, Any])
async def database_statistics(current_user: UserResponse = Depends(get_current_user)):
    """Get database statistics (admin only)"""
    try:
        return await database_service.get_database_statistics()
    except Exception as e:
        logger.error(f"Failed to get database statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database statistics")

@router.post("/database/optimize", response_model=Dict[str, Any])
async def optimize_database(current_user: UserResponse = Depends(get_current_user)):
    """Run database optimization tasks (admin only)"""
    try:
        result = await database_service.optimize_database()
        return result
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Database optimization failed")

@router.post("/database/migrations", response_model=Dict[str, Any])
async def run_migrations(current_user: UserResponse = Depends(get_current_user)):
    """Run pending database migrations (admin only)"""
    try:
        result = await database_service.run_migrations()
        return result
    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        raise HTTPException(status_code=500, detail="Migration execution failed")

@router.get("/system", response_model=List[Dict[str, Any]])
async def system_health_history(
    component: Optional[str] = Query(None, description="Filter by component"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get system health history"""
    try:
        return await database_service.get_system_health_history(component, hours)
    except Exception as e:
        logger.error(f"Failed to get system health history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health history")

@router.get("/audit", response_model=List[Dict[str, Any]])
async def audit_logs(
    limit: int = Query(50, ge=1, le=1000, description="Number of records to retrieve"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get audit logs for current user"""
    try:
        return await database_service.get_audit_logs(current_user.id, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_data(
    retention_days: int = Query(90, ge=30, le=365, description="Data retention period in days"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Clean up old data based on retention policy (admin only)"""
    try:
        result = await database_service.cleanup_old_data(retention_days)
        
        # Log the cleanup action
        await database_service.log_audit_event(
            user_id=current_user.id,
            action="data_cleanup",
            resource_type="system",
            new_values={"retention_days": retention_days, "result": result}
        )
        
        return result
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Data cleanup failed")