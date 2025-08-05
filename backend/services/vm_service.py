from typing import List, Optional, Dict, Any
from datetime import datetime
from models import (
    VMCreate, VMResponse, VMStatus, InstanceType, VMImage, 
    INSTANCE_SPECS, UserResponse, APIResponse
)
from .base_service import BaseService, ServiceError, ValidationError, NotFoundError, InsufficientCreditsError
import random

class VMService(BaseService):
    """Virtual Machine management service"""
    
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
    
    async def create_vm(self, vm_data: VMCreate, user: UserResponse) -> VMResponse:
        """Create a new virtual machine"""
        try:
            # Validate VM creation request
            await self._validate_vm_creation(vm_data, user)
            
            # Check if project exists and belongs to user
            if not await self.validate_user_ownership(user.id, "projects", vm_data.project_id):
                raise NotFoundError("Project", vm_data.project_id)
            
            # Check if VM name is unique within project
            if await self._vm_name_exists_in_project(vm_data.name, vm_data.project_id):
                raise ValidationError(f"VM name '{vm_data.name}' already exists in this project")
            
            # Check user credits
            cost_per_hour = INSTANCE_SPECS[vm_data.instance_type]["cost_per_hour"]
            creation_cost = 0.05  # One-time creation cost
            
            if user.credits < creation_cost:
                raise InsufficientCreditsError(creation_cost, user.credits)
            
            # Generate VM record
            vm_record = {
                "id": self.generate_id(),
                "name": vm_data.name,
                "instance_type": vm_data.instance_type.value,
                "image": vm_data.image.value,
                "status": VMStatus.CREATING.value,
                "ip_address": self._generate_ip_address(),
                "user_id": user.id,
                "project_id": vm_data.project_id,
                "cost_per_hour": cost_per_hour,
                "uptime_hours": 0.0,
                "total_cost": creation_cost,
                "current_session_hours": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": None,
                "last_started": None,
                "last_stopped": None
            }
            
            # Create VM in database
            created_vm = await self._create_vm_record(vm_record)
            if not created_vm:
                raise ServiceError("Failed to create VM", "VM_CREATION_FAILED")
            
            # Deduct creation cost from user credits
            new_credits = user.credits - creation_cost
            await self.update_user_credits(user.id, new_credits)
            
            # Record billing transaction
            await self.billing_service.record_transaction(
                user_id=user.id,
                vm_id=created_vm["id"],
                action_type="vm_create",
                amount=creation_cost,
                description=f"VM creation: {vm_data.name} ({vm_data.instance_type.value})"
            )
            
            # Start VM automatically
            await self._update_vm_status(created_vm["id"], VMStatus.RUNNING.value)
            created_vm["status"] = VMStatus.RUNNING.value
            created_vm["last_started"] = datetime.utcnow()
            
            # Log audit event
            await self.log_audit_event(
                user_id=user.id,
                action="vm_create",
                resource_type="vms",
                resource_id=created_vm["id"],
                details={
                    "name": vm_data.name,
                    "instance_type": vm_data.instance_type.value,
                    "image": vm_data.image.value,
                    "project_id": vm_data.project_id
                }
            )
            
            return self._build_vm_response(created_vm)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"VM creation error: {e}")
            raise ServiceError("Internal server error during VM creation", "VM_CREATION_ERROR")
    
    async def get_vm(self, vm_id: str, user_id: str) -> VMResponse:
        """Get a specific VM by ID"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            vm_record = await self._get_vm_by_id(vm_id)
            if not vm_record:
                raise NotFoundError("VM", vm_id)
            
            return self._build_vm_response(vm_record)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting VM: {e}")
            raise ServiceError("Failed to retrieve VM", "VM_RETRIEVAL_ERROR")
    
    async def get_user_vms(self, user_id: str, project_id: Optional[str] = None) -> List[VMResponse]:
        """Get all VMs for a user, optionally filtered by project"""
        try:
            vms = await self._get_vms_by_user(user_id, project_id)
            return [self._build_vm_response(vm) for vm in vms]
            
        except Exception as e:
            self.logger.error(f"Error getting user VMs: {e}")
            raise ServiceError("Failed to retrieve VMs", "VM_RETRIEVAL_ERROR")
    
    async def start_vm(self, vm_id: str, user_id: str) -> APIResponse:
        """Start a stopped VM"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            vm_record = await self._get_vm_by_id(vm_id)
            if not vm_record:
                raise NotFoundError("VM", vm_id)
            
            current_status = VMStatus(vm_record["status"])
            
            if current_status == VMStatus.RUNNING:
                raise ValidationError("VM is already running")
            
            if current_status == VMStatus.TERMINATED:
                raise ValidationError("Cannot start a terminated VM")
            
            # Update VM status and timestamps
            update_data = {
                "status": VMStatus.RUNNING.value,
                "last_started": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self._update_vm_record(vm_id, update_data)
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="vm_start",
                resource_type="vms",
                resource_id=vm_id,
                details={"vm_name": vm_record["name"]}
            )
            
            return self.create_success_response("VM started successfully")
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error starting VM: {e}")
            raise ServiceError("Failed to start VM", "VM_START_ERROR")
    
    async def stop_vm(self, vm_id: str, user_id: str) -> APIResponse:
        """Stop a running VM"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            vm_record = await self._get_vm_by_id(vm_id)
            if not vm_record:
                raise NotFoundError("VM", vm_id)
            
            current_status = VMStatus(vm_record["status"])
            
            if current_status == VMStatus.STOPPED:
                raise ValidationError("VM is already stopped")
            
            if current_status == VMStatus.TERMINATED:
                raise ValidationError("Cannot stop a terminated VM")
            
            # Calculate session cost if VM was running
            if current_status == VMStatus.RUNNING and vm_record.get("last_started"):
                session_hours = self._calculate_session_hours(vm_record["last_started"])
                session_cost = session_hours * vm_record.get("cost_per_hour", 0.0)
                
                # Update total cost and uptime
                new_total_cost = vm_record.get("total_cost", 0.0) + session_cost
                new_uptime = vm_record.get("uptime_hours", 0.0) + session_hours
                
                # Deduct session cost from user credits
                current_credits = await self.get_user_credits(user_id)
                if current_credits >= session_cost:
                    await self.update_user_credits(user_id, current_credits - session_cost)
                    
                    # Record billing transaction
                    await self.billing_service.record_transaction(
                        user_id=user_id,
                        vm_id=vm_id,
                        action_type="vm_usage",
                        amount=session_cost,
                        description=f"VM usage: {vm_record['name']} ({session_hours:.2f} hours)"
                    )
                
                update_data = {
                    "status": VMStatus.STOPPED.value,
                    "last_stopped": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "total_cost": new_total_cost,
                    "uptime_hours": new_uptime,
                    "current_session_hours": 0.0
                }
            else:
                update_data = {
                    "status": VMStatus.STOPPED.value,
                    "last_stopped": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            
            await self._update_vm_record(vm_id, update_data)
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="vm_stop",
                resource_type="vms",
                resource_id=vm_id,
                details={"vm_name": vm_record["name"]}
            )
            
            return self.create_success_response("VM stopped successfully")
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error stopping VM: {e}")
            raise ServiceError("Failed to stop VM", "VM_STOP_ERROR")
    
    async def restart_vm(self, vm_id: str, user_id: str) -> APIResponse:
        """Restart a VM (stop then start)"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            vm_record = await self._get_vm_by_id(vm_id)
            if not vm_record:
                raise NotFoundError("VM", vm_id)
            
            current_status = VMStatus(vm_record["status"])
            
            if current_status == VMStatus.TERMINATED:
                raise ValidationError("Cannot restart a terminated VM")
            
            # Stop the VM if it's running
            if current_status == VMStatus.RUNNING:
                await self.stop_vm(vm_id, user_id)
            
            # Start the VM
            await self.start_vm(vm_id, user_id)
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="vm_restart",
                resource_type="vms",
                resource_id=vm_id,
                details={"vm_name": vm_record["name"]}
            )
            
            return self.create_success_response("VM restarted successfully")
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error restarting VM: {e}")
            raise ServiceError("Failed to restart VM", "VM_RESTART_ERROR")
    
    async def delete_vm(self, vm_id: str, user_id: str) -> APIResponse:
        """Delete/terminate a VM"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            vm_record = await self._get_vm_by_id(vm_id)
            if not vm_record:
                raise NotFoundError("VM", vm_id)
            
            current_status = VMStatus(vm_record["status"])
            
            if current_status == VMStatus.TERMINATED:
                raise ValidationError("VM is already terminated")
            
            # Calculate final costs if VM was running
            if current_status == VMStatus.RUNNING and vm_record.get("last_started"):
                session_hours = self._calculate_session_hours(vm_record["last_started"])
                session_cost = session_hours * vm_record.get("cost_per_hour", 0.0)
                
                # Update total cost and uptime
                new_total_cost = vm_record.get("total_cost", 0.0) + session_cost
                new_uptime = vm_record.get("uptime_hours", 0.0) + session_hours
                
                # Deduct session cost from user credits
                current_credits = await self.get_user_credits(user_id)
                if current_credits >= session_cost:
                    await self.update_user_credits(user_id, current_credits - session_cost)
                    
                    # Record billing transaction
                    await self.billing_service.record_transaction(
                        user_id=user_id,
                        vm_id=vm_id,
                        action_type="vm_usage",
                        amount=session_cost,
                        description=f"Final VM usage: {vm_record['name']} ({session_hours:.2f} hours)"
                    )
                
                update_data = {
                    "status": VMStatus.TERMINATED.value,
                    "updated_at": datetime.utcnow(),
                    "total_cost": new_total_cost,
                    "uptime_hours": new_uptime,
                    "current_session_hours": 0.0
                }
            else:
                update_data = {
                    "status": VMStatus.TERMINATED.value,
                    "updated_at": datetime.utcnow()
                }
            
            await self._update_vm_record(vm_id, update_data)
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="vm_delete",
                resource_type="vms",
                resource_id=vm_id,
                details={"vm_name": vm_record["name"]}
            )
            
            return self.create_success_response("VM terminated successfully")
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting VM: {e}")
            raise ServiceError("Failed to delete VM", "VM_DELETE_ERROR")
    
    async def health_check(self) -> Dict[str, Any]:
        """VM service health check"""
        try:
            return {
                "service": "vm",
                "status": "healthy",
                "database_connection": "ok",
                "vm_operations": "ok"
            }
        except Exception as e:
            return {
                "service": "vm",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_vm_creation(self, vm_data: VMCreate, user: UserResponse):
        """Validate VM creation request"""
        if vm_data.instance_type not in INSTANCE_SPECS:
            raise ValidationError(f"Invalid instance type: {vm_data.instance_type}")
        
        if not vm_data.name.strip():
            raise ValidationError("VM name cannot be empty")
        
        reserved_names = ['admin', 'root', 'system', 'api', 'www']
        if vm_data.name.lower() in reserved_names:
            raise ValidationError(f"VM name '{vm_data.name}' is reserved")
    
    async def _vm_name_exists_in_project(self, name: str, project_id: str) -> bool:
        """Check if VM name exists in project"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").select("id").eq("name", name).eq("project_id", project_id).neq("status", "terminated").execute()
                return bool(result.data)
            else:
                memory_store = self.db.get_memory_store()
                for vm in memory_store["vms"]:
                    if (vm.get("name") == name and 
                        vm.get("project_id") == project_id and 
                        vm.get("status") != "terminated"):
                        return True
                return False
        except Exception as e:
            self.logger.error(f"Error checking VM name existence: {e}")
            return False
    
    def _generate_ip_address(self) -> str:
        """Generate a random IP address for simulation"""
        return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
    
    async def _create_vm_record(self, vm_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create VM record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").insert(vm_record).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                memory_store["vms"].append(vm_record)
                return vm_record
        except Exception as e:
            self.logger.error(f"Error creating VM record: {e}")
            return None
    
    async def _update_vm_status(self, vm_id: str, status: str):
        """Update VM status"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                supabase.table("vms").update({"status": status, "updated_at": datetime.utcnow()}).eq("id", vm_id).execute()
            else:
                memory_store = self.db.get_memory_store()
                for vm in memory_store["vms"]:
                    if vm.get("id") == vm_id:
                        vm["status"] = status
                        vm["updated_at"] = datetime.utcnow()
                        break
        except Exception as e:
            self.logger.error(f"Error updating VM status: {e}")
    
    async def _get_vm_by_id(self, vm_id: str) -> Optional[Dict[str, Any]]:
        """Get VM by ID"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").select("*").eq("id", vm_id).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                for vm in memory_store["vms"]:
                    if vm.get("id") == vm_id:
                        return vm
                return None
        except Exception as e:
            self.logger.error(f"Error getting VM by ID: {e}")
            return None
    
    async def _get_vms_by_user(self, user_id: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get VMs by user, optionally filtered by project"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                query = supabase.table("vms").select("*").eq("user_id", user_id)
                
                if project_id:
                    query = query.eq("project_id", project_id)
                
                result = query.order("created_at", desc=True).execute()
                return result.data or []
            else:
                memory_store = self.db.get_memory_store()
                vms = [
                    vm for vm in memory_store["vms"] 
                    if vm.get("user_id") == user_id
                ]
                
                if project_id:
                    vms = [vm for vm in vms if vm.get("project_id") == project_id]
                
                return sorted(vms, key=lambda x: x.get("created_at", datetime.min), reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting VMs by user: {e}")
            return []
    
    async def _update_vm_record(self, vm_id: str, update_data: Dict[str, Any]) -> bool:
        """Update VM record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").update(update_data).eq("id", vm_id).execute()
                return bool(result.data)
            else:
                memory_store = self.db.get_memory_store()
                for vm in memory_store["vms"]:
                    if vm.get("id") == vm_id:
                        vm.update(update_data)
                        return True
                return False
        except Exception as e:
            self.logger.error(f"Error updating VM record: {e}")
            return False
    
    def _calculate_session_hours(self, start_time) -> float:
        """Calculate hours between start time and now"""
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            elif isinstance(start_time, datetime):
                pass
            else:
                return 0.0
            
            duration = datetime.utcnow() - start_time.replace(tzinfo=None)
            return duration.total_seconds() / 3600
        except Exception as e:
            self.logger.error(f"Error calculating session hours: {e}")
            return 0.0

    def _build_vm_response(self, vm_record: Dict[str, Any]) -> VMResponse:
        """Build VM response from database record"""
        # Get instance specs
        instance_type = InstanceType(vm_record["instance_type"])
        specs = {
            "cpu": INSTANCE_SPECS[instance_type]["cpu"],
            "ram": INSTANCE_SPECS[instance_type]["ram"],
            "storage": INSTANCE_SPECS[instance_type]["storage"]
        }
        
        return VMResponse(
            id=vm_record["id"],
            name=vm_record["name"],
            instance_type=instance_type,
            image=VMImage(vm_record["image"]),
            status=VMStatus(vm_record["status"]),
            ip_address=vm_record.get("ip_address"),
            user_id=vm_record["user_id"],
            project_id=vm_record["project_id"],
            specs=specs,
            cost_per_hour=vm_record.get("cost_per_hour", 0.0),
            uptime_hours=vm_record.get("uptime_hours", 0.0),
            total_cost=vm_record.get("total_cost", 0.0),
            current_session_hours=vm_record.get("current_session_hours", 0.0),
            created_at=vm_record["created_at"],
            updated_at=vm_record.get("updated_at"),
            last_started=vm_record.get("last_started"),
            last_stopped=vm_record.get("last_stopped")
        )