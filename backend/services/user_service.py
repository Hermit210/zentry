from typing import List, Optional, Dict, Any
from datetime import datetime
from models import UserResponse, CreditUpdate
from .base_service import BaseService, ServiceError, ValidationError, NotFoundError

class UserService(BaseService):
    """User management service"""
    
    def __init__(self):
        super().__init__()
        self._billing_service = None
    
    @property
    def billing_service(self):
        """Lazy load billing service to avoid circular imports"""
        if self._billing_service is None:
            from .billing_service import BillingService
            self._billing_service = BillingService()
        return self._billing_service
    
    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Get user by ID with updated statistics"""
        try:
            user_record = await self._get_user_record(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Update user statistics
            stats = await self._calculate_user_stats(user_id)
            user_record.update(stats)
            
            return UserResponse(**user_record)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting user: {e}")
            raise ServiceError("Failed to retrieve user", "USER_RETRIEVAL_ERROR")
    
    async def add_user_credits(self, user_id: str, credit_data: CreditUpdate) -> UserResponse:
        """Add credits to user account"""
        try:
            # Validate user exists
            user_record = await self._get_user_record(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Add credits using billing service
            await self.billing_service.add_credits(
                user_id=user_id,
                amount=credit_data.amount,
                description=credit_data.description or f"Credit addition: ${credit_data.amount:.2f}"
            )
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="credits_add",
                resource_type="users",
                resource_id=user_id,
                details={
                    "amount": credit_data.amount,
                    "description": credit_data.description
                }
            )
            
            # Return updated user
            return await self.get_user_by_id(user_id)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error adding user credits: {e}")
            raise ServiceError("Failed to add credits", "CREDIT_ADD_ERROR")
    
    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        try:
            # Get user info
            user = await self.get_user_by_id(user_id)
            
            # Get usage summary
            usage_summary = await self.billing_service.get_usage_summary(user_id)
            
            # Get VM costs
            vm_costs = await self.billing_service.calculate_vm_costs(user_id)
            
            # Get recent billing history
            recent_billing = await self.billing_service.get_user_billing_history(user_id, limit=10)
            
            # Get resource counts
            resource_stats = await self._get_resource_statistics(user_id)
            
            return {
                "user": user,
                "usage_summary": usage_summary,
                "vm_costs": vm_costs,
                "recent_billing": recent_billing,
                "resource_stats": resource_stats,
                "dashboard_updated": datetime.utcnow()
            }
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            raise ServiceError("Failed to retrieve dashboard data", "DASHBOARD_ERROR")
    
    async def get_user_activity_log(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's recent activity log"""
        try:
            # Get audit logs for user
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("audit_logs").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(limit).execute()
                logs = result.data or []
            else:
                memory_store = self.db.get_memory_store()
                logs = [
                    log for log in memory_store["audit_logs"]
                    if log.get("user_id") == user_id
                ]
                logs = sorted(logs, key=lambda x: x.get("timestamp", datetime.min), reverse=True)[:limit]
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting user activity log: {e}")
            raise ServiceError("Failed to retrieve activity log", "ACTIVITY_LOG_ERROR")
    
    async def deactivate_user(self, user_id: str, admin_user_id: str) -> UserResponse:
        """Deactivate a user account (admin only)"""
        try:
            # Validate admin permissions (simplified for now)
            admin_user = await self._get_user_record(admin_user_id)
            if not admin_user or admin_user.get("role") != "admin":
                raise ServiceError("Insufficient permissions", "PERMISSION_DENIED")
            
            # Get target user
            user_record = await self._get_user_record(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Update user status
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
            
            updated_user = await self._update_user_record(user_id, update_data)
            if not updated_user:
                raise ServiceError("Failed to deactivate user", "USER_DEACTIVATION_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=admin_user_id,
                action="user_deactivate",
                resource_type="users",
                resource_id=user_id,
                details={
                    "target_user_email": user_record["email"],
                    "admin_action": True
                }
            )
            
            return UserResponse(**updated_user)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error deactivating user: {e}")
            raise ServiceError("Failed to deactivate user", "USER_DEACTIVATION_ERROR")
    
    async def reactivate_user(self, user_id: str, admin_user_id: str) -> UserResponse:
        """Reactivate a user account (admin only)"""
        try:
            # Validate admin permissions
            admin_user = await self._get_user_record(admin_user_id)
            if not admin_user or admin_user.get("role") != "admin":
                raise ServiceError("Insufficient permissions", "PERMISSION_DENIED")
            
            # Get target user
            user_record = await self._get_user_record(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Update user status
            update_data = {
                "is_active": True,
                "updated_at": datetime.utcnow()
            }
            
            updated_user = await self._update_user_record(user_id, update_data)
            if not updated_user:
                raise ServiceError("Failed to reactivate user", "USER_REACTIVATION_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=admin_user_id,
                action="user_reactivate",
                resource_type="users",
                resource_id=user_id,
                details={
                    "target_user_email": user_record["email"],
                    "admin_action": True
                }
            )
            
            return UserResponse(**updated_user)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error reactivating user: {e}")
            raise ServiceError("Failed to reactivate user", "USER_REACTIVATION_ERROR")
    
    async def health_check(self) -> Dict[str, Any]:
        """User service health check"""
        try:
            # Test user lookup functionality
            test_result = await self._get_user_record("test-user-id")
            
            return {
                "service": "user",
                "status": "healthy",
                "database_connection": "ok",
                "user_operations": "ok"
            }
        except Exception as e:
            return {
                "service": "user",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_user_record(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user record from database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").select("*").eq("id", user_id).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                for user_data in memory_store["users"].values():
                    if user_data.get("id") == user_id:
                        return user_data
                return None
        except Exception as e:
            self.logger.error(f"Error getting user record: {e}")
            return None
    
    async def _update_user_record(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").update(update_data).eq("id", user_id).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                for email, user_data in memory_store["users"].items():
                    if user_data.get("id") == user_id:
                        user_data.update(update_data)
                        return user_data
                return None
        except Exception as e:
            self.logger.error(f"Error updating user record: {e}")
            return None
    
    async def _calculate_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Calculate user statistics"""
        try:
            stats = {
                "vm_count": 0,
                "project_count": 0,
                "active_vm_count": 0,
                "total_spent": 0.0
            }
            
            if self.db.get_client():
                supabase = self.db.get_client()
                
                # Count VMs
                vm_result = supabase.table("vms").select("*", count="exact").eq("user_id", user_id).execute()
                stats["vm_count"] = vm_result.count or 0
                
                # Count active VMs
                active_vm_result = supabase.table("vms").select("*", count="exact").eq("user_id", user_id).eq("status", "running").execute()
                stats["active_vm_count"] = active_vm_result.count or 0
                
                # Count projects
                project_result = supabase.table("projects").select("*", count="exact").eq("user_id", user_id).execute()
                stats["project_count"] = project_result.count or 0
                
                # Calculate total spent
                billing_result = supabase.table("billing_records").select("amount").eq("user_id", user_id).execute()
                if billing_result.data:
                    stats["total_spent"] = sum(float(record["amount"]) for record in billing_result.data if float(record["amount"]) > 0)
            else:
                memory_store = self.db.get_memory_store()
                
                # Count VMs
                stats["vm_count"] = len([vm for vm in memory_store["vms"] if vm.get("user_id") == user_id])
                
                # Count active VMs
                stats["active_vm_count"] = len([vm for vm in memory_store["vms"] if vm.get("user_id") == user_id and vm.get("status") == "running"])
                
                # Count projects
                stats["project_count"] = len([project for project in memory_store["projects"] if project.get("user_id") == user_id])
                
                # Calculate total spent
                stats["total_spent"] = sum(
                    float(record["amount"]) for record in memory_store["billing_records"]
                    if record.get("user_id") == user_id and float(record["amount"]) > 0
                )
            
            return stats
        except Exception as e:
            self.logger.error(f"Error calculating user stats: {e}")
            return {
                "vm_count": 0,
                "project_count": 0,
                "active_vm_count": 0,
                "total_spent": 0.0
            }
    
    async def _get_resource_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed resource statistics"""
        try:
            stats = await self._calculate_user_stats(user_id)
            
            # Add more detailed breakdowns
            if self.db.get_client():
                supabase = self.db.get_client()
                
                # VM status breakdown
                vm_statuses = {}
                vm_result = supabase.table("vms").select("status").eq("user_id", user_id).execute()
                for vm in vm_result.data or []:
                    status = vm["status"]
                    vm_statuses[status] = vm_statuses.get(status, 0) + 1
                
                # Instance type breakdown
                instance_types = {}
                instance_result = supabase.table("vms").select("instance_type").eq("user_id", user_id).execute()
                for vm in instance_result.data or []:
                    instance_type = vm["instance_type"]
                    instance_types[instance_type] = instance_types.get(instance_type, 0) + 1
                
                stats.update({
                    "vm_status_breakdown": vm_statuses,
                    "instance_type_breakdown": instance_types
                })
            else:
                memory_store = self.db.get_memory_store()
                user_vms = [vm for vm in memory_store["vms"] if vm.get("user_id") == user_id]
                
                # VM status breakdown
                vm_statuses = {}
                for vm in user_vms:
                    status = vm.get("status", "unknown")
                    vm_statuses[status] = vm_statuses.get(status, 0) + 1
                
                # Instance type breakdown
                instance_types = {}
                for vm in user_vms:
                    instance_type = vm.get("instance_type", "unknown")
                    instance_types[instance_type] = instance_types.get(instance_type, 0) + 1
                
                stats.update({
                    "vm_status_breakdown": vm_statuses,
                    "instance_type_breakdown": instance_types
                })
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting resource statistics: {e}")
            return {}