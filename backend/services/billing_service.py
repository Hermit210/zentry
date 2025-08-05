from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import BillingRecord, BillingRecordCreate, BillingActionType, UsageSummary
from .base_service import BaseService, ServiceError, ValidationError

class BillingService(BaseService):
    """Billing and credit management service"""
    
    async def record_transaction(self, user_id: str, action_type: str, amount: float, description: str, vm_id: Optional[str] = None) -> BillingRecord:
        """Record a billing transaction"""
        try:
            # Validate transaction data
            await self._validate_transaction(user_id, action_type, amount, description)
            
            # Create billing record
            billing_record = {
                "id": self.generate_id(),
                "user_id": user_id,
                "vm_id": vm_id,
                "action_type": action_type,
                "amount": amount,
                "description": description,
                "created_at": datetime.utcnow()
            }
            
            # Save to database
            created_record = await self._create_billing_record(billing_record)
            if not created_record:
                raise ServiceError("Failed to record billing transaction", "BILLING_RECORD_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="billing_transaction",
                resource_type="billing_records",
                resource_id=created_record["id"],
                details={
                    "action_type": action_type,
                    "amount": amount,
                    "vm_id": vm_id
                }
            )
            
            return BillingRecord(**created_record)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Billing transaction error: {e}")
            raise ServiceError("Internal server error during billing transaction", "BILLING_ERROR")
    
    async def get_user_billing_history(self, user_id: str, limit: int = 50, action_type: Optional[BillingActionType] = None) -> List[BillingRecord]:
        """Get user's billing history"""
        try:
            records = await self._get_billing_records_by_user(user_id, limit, action_type)
            return [BillingRecord(**record) for record in records]
        except Exception as e:
            self.logger.error(f"Error getting billing history: {e}")
            raise ServiceError("Failed to retrieve billing history", "BILLING_HISTORY_ERROR")
    
    async def get_usage_summary(self, user_id: str, period_days: int = 30) -> UsageSummary:
        """Get user's usage summary for a period"""
        try:
            # Calculate period dates
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get user's current credits
            current_credits = await self.get_user_credits(user_id)
            
            # Calculate spending statistics
            spending_stats = await self._calculate_spending_stats(user_id, start_date, end_date)
            
            # Get VM statistics
            vm_stats = await self._get_vm_statistics(user_id)
            
            # Calculate current hourly cost
            hourly_cost = await self._calculate_current_hourly_cost(user_id)
            
            return UsageSummary(
                user_id=user_id,
                current_credits=current_credits,
                total_spent=spending_stats["total_spent"],
                active_vms=vm_stats["active_vms"],
                total_vms=vm_stats["total_vms"],
                billing_records_count=spending_stats["record_count"],
                period_start=start_date,
                period_end=end_date,
                hourly_cost=hourly_cost,
                projected_monthly_cost=hourly_cost * 24 * 30
            )
            
        except Exception as e:
            self.logger.error(f"Error getting usage summary: {e}")
            raise ServiceError("Failed to retrieve usage summary", "USAGE_SUMMARY_ERROR")
    
    async def add_credits(self, user_id: str, amount: float, description: str = "Credit addition") -> BillingRecord:
        """Add credits to user account"""
        try:
            if amount <= 0:
                raise ValidationError("Credit amount must be positive")
            
            # Get current credits
            current_credits = await self.get_user_credits(user_id)
            
            # Update user credits
            new_credits = current_credits + amount
            success = await self.update_user_credits(user_id, new_credits)
            if not success:
                raise ServiceError("Failed to update user credits", "CREDIT_UPDATE_FAILED")
            
            # Record the transaction
            return await self.record_transaction(
                user_id=user_id,
                action_type=BillingActionType.CREDIT_ADD.value,
                amount=amount,
                description=description
            )
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error adding credits: {e}")
            raise ServiceError("Failed to add credits", "CREDIT_ADD_ERROR")
    
    async def deduct_credits(self, user_id: str, amount: float, description: str = "Credit deduction") -> BillingRecord:
        """Deduct credits from user account"""
        try:
            if amount <= 0:
                raise ValidationError("Deduction amount must be positive")
            
            # Get current credits
            current_credits = await self.get_user_credits(user_id)
            
            if current_credits < amount:
                raise ValidationError(f"Insufficient credits. Available: ${current_credits:.2f}, Required: ${amount:.2f}")
            
            # Update user credits
            new_credits = current_credits - amount
            success = await self.update_user_credits(user_id, new_credits)
            if not success:
                raise ServiceError("Failed to update user credits", "CREDIT_UPDATE_FAILED")
            
            # Record the transaction
            return await self.record_transaction(
                user_id=user_id,
                action_type=BillingActionType.CREDIT_DEDUCT.value,
                amount=-amount,  # Negative for deduction
                description=description
            )
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error deducting credits: {e}")
            raise ServiceError("Failed to deduct credits", "CREDIT_DEDUCT_ERROR")
    
    async def calculate_vm_costs(self, user_id: str) -> Dict[str, Any]:
        """Calculate VM costs for user"""
        try:
            # Get all user's VMs
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").select("*").eq("user_id", user_id).execute()
                vms = result.data or []
            else:
                memory_store = self.db.get_memory_store()
                vms = [vm for vm in memory_store["vms"] if vm.get("user_id") == user_id]
            
            total_cost = 0.0
            running_cost_per_hour = 0.0
            vm_costs = []
            
            for vm in vms:
                vm_total_cost = float(vm.get("total_cost", 0.0))
                vm_cost_per_hour = float(vm.get("cost_per_hour", 0.0))
                
                total_cost += vm_total_cost
                
                if vm.get("status") == "running":
                    running_cost_per_hour += vm_cost_per_hour
                
                vm_costs.append({
                    "vm_id": vm["id"],
                    "vm_name": vm["name"],
                    "status": vm["status"],
                    "total_cost": vm_total_cost,
                    "cost_per_hour": vm_cost_per_hour,
                    "uptime_hours": float(vm.get("uptime_hours", 0.0))
                })
            
            return {
                "total_cost": total_cost,
                "running_cost_per_hour": running_cost_per_hour,
                "projected_daily_cost": running_cost_per_hour * 24,
                "projected_monthly_cost": running_cost_per_hour * 24 * 30,
                "vm_costs": vm_costs
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating VM costs: {e}")
            raise ServiceError("Failed to calculate VM costs", "COST_CALCULATION_ERROR")
    
    async def health_check(self) -> Dict[str, Any]:
        """Billing service health check"""
        try:
            # Test billing record lookup
            test_result = await self._get_billing_records_by_user("test-user-id", 1)
            
            return {
                "service": "billing",
                "status": "healthy",
                "database_connection": "ok",
                "billing_operations": "ok"
            }
        except Exception as e:
            return {
                "service": "billing",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_transaction(self, user_id: str, action_type: str, amount: float, description: str):
        """Validate billing transaction data"""
        if not user_id:
            raise ValidationError("User ID is required")
        
        if not action_type:
            raise ValidationError("Action type is required")
        
        if amount == 0:
            raise ValidationError("Amount cannot be zero")
        
        if not description:
            raise ValidationError("Description is required")
    
    async def _create_billing_record(self, billing_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create billing record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("billing_records").insert(billing_record).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                memory_store["billing_records"].append(billing_record)
                return billing_record
        except Exception as e:
            self.logger.error(f"Error creating billing record: {e}")
            return None
    
    async def _get_billing_records_by_user(self, user_id: str, limit: int = 50, action_type: Optional[BillingActionType] = None) -> List[Dict[str, Any]]:
        """Get billing records by user"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                query = supabase.table("billing_records").select("*").eq("user_id", user_id)
                
                if action_type:
                    query = query.eq("action_type", action_type.value)
                
                result = query.order("created_at", desc=True).limit(limit).execute()
                return result.data or []
            else:
                memory_store = self.db.get_memory_store()
                records = [
                    record for record in memory_store["billing_records"] 
                    if record.get("user_id") == user_id
                ]
                
                if action_type:
                    records = [
                        record for record in records 
                        if record.get("action_type") == action_type.value
                    ]
                
                # Sort by created_at descending and limit
                records = sorted(records, key=lambda x: x.get("created_at", datetime.min), reverse=True)
                return records[:limit]
        except Exception as e:
            self.logger.error(f"Error getting billing records: {e}")
            return []
    
    async def _calculate_spending_stats(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate spending statistics for a period"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("billing_records").select("amount").eq("user_id", user_id).gte("created_at", start_date.isoformat()).lte("created_at", end_date.isoformat()).execute()
                records = result.data or []
            else:
                memory_store = self.db.get_memory_store()
                records = [
                    record for record in memory_store["billing_records"]
                    if (record.get("user_id") == user_id and
                        start_date <= datetime.fromisoformat(record.get("created_at", "1970-01-01")) <= end_date)
                ]
            
            total_spent = sum(float(record["amount"]) for record in records if float(record["amount"]) > 0)
            
            return {
                "total_spent": total_spent,
                "record_count": len(records)
            }
        except Exception as e:
            self.logger.error(f"Error calculating spending stats: {e}")
            return {"total_spent": 0.0, "record_count": 0}
    
    async def _get_vm_statistics(self, user_id: str) -> Dict[str, int]:
        """Get VM statistics for user"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                
                # Total VMs
                total_result = supabase.table("vms").select("*", count="exact").eq("user_id", user_id).execute()
                total_vms = total_result.count or 0
                
                # Active VMs
                active_result = supabase.table("vms").select("*", count="exact").eq("user_id", user_id).eq("status", "running").execute()
                active_vms = active_result.count or 0
            else:
                memory_store = self.db.get_memory_store()
                user_vms = [vm for vm in memory_store["vms"] if vm.get("user_id") == user_id]
                total_vms = len(user_vms)
                active_vms = len([vm for vm in user_vms if vm.get("status") == "running"])
            
            return {
                "total_vms": total_vms,
                "active_vms": active_vms
            }
        except Exception as e:
            self.logger.error(f"Error getting VM statistics: {e}")
            return {"total_vms": 0, "active_vms": 0}
    
    async def _calculate_current_hourly_cost(self, user_id: str) -> float:
        """Calculate current hourly cost for running VMs"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").select("cost_per_hour").eq("user_id", user_id).eq("status", "running").execute()
                vms = result.data or []
            else:
                memory_store = self.db.get_memory_store()
                vms = [
                    vm for vm in memory_store["vms"] 
                    if vm.get("user_id") == user_id and vm.get("status") == "running"
                ]
            
            return sum(float(vm.get("cost_per_hour", 0.0)) for vm in vms)
        except Exception as e:
            self.logger.error(f"Error calculating hourly cost: {e}")
            return 0.0