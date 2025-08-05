from typing import List, Optional, Dict, Any
from datetime import datetime
from models import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithVMs, VMResponse
from .base_service import BaseService, ServiceError, ValidationError, NotFoundError

class ProjectService(BaseService):
    """Project management service"""
    
    def __init__(self):
        super().__init__()
        self._vm_service = None
    
    @property
    def vm_service(self):
        """Lazy load VM service to avoid circular imports"""
        if self._vm_service is None:
            from .vm_service import VMService
            self._vm_service = VMService()
        return self._vm_service
    
    async def create_project(self, project_data: ProjectCreate, user_id: str) -> ProjectResponse:
        """Create a new project"""
        try:
            # Validate project creation
            await self._validate_project_creation(project_data, user_id)
            
            # Check if project name is unique for user
            if await self._project_name_exists_for_user(project_data.name, user_id):
                raise ValidationError(f"Project name '{project_data.name}' already exists")
            
            # Create project record
            project_record = {
                "id": self.generate_id(),
                "name": project_data.name,
                "description": project_data.description or "",
                "user_id": user_id,
                "vm_count": 0,
                "active_vm_count": 0,
                "total_cost": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            
            # Save project to database
            created_project = await self._create_project_record(project_record)
            if not created_project:
                raise ServiceError("Failed to create project", "PROJECT_CREATION_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="project_create",
                resource_type="projects",
                resource_id=created_project["id"],
                details={
                    "name": project_data.name,
                    "description": project_data.description
                }
            )
            
            return ProjectResponse(**created_project)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Project creation error: {e}")
            raise ServiceError("Internal server error during project creation", "PROJECT_CREATION_ERROR")
    
    async def get_user_projects(self, user_id: str) -> List[ProjectResponse]:
        """Get all projects for a user"""
        try:
            projects = await self._get_projects_by_user(user_id)
            
            # Update project statistics
            for project in projects:
                stats = await self._calculate_project_stats(project["id"])
                project.update(stats)
            
            return [ProjectResponse(**project) for project in projects]
            
        except Exception as e:
            self.logger.error(f"Error getting user projects: {e}")
            raise ServiceError("Failed to retrieve projects", "PROJECT_RETRIEVAL_ERROR")
    
    async def get_project(self, project_id: str, user_id: str, include_vms: bool = False) -> ProjectResponse:
        """Get a specific project"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "projects", project_id):
                raise NotFoundError("Project", project_id)
            
            project_record = await self._get_project_by_id(project_id)
            if not project_record:
                raise NotFoundError("Project", project_id)
            
            # Update project statistics
            stats = await self._calculate_project_stats(project_id)
            project_record.update(stats)
            
            if include_vms:
                # Get VMs for this project
                vms = await self.vm_service.get_user_vms(user_id, project_id=project_id)
                return ProjectWithVMs(**project_record, vms=vms)
            
            return ProjectResponse(**project_record)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting project: {e}")
            raise ServiceError("Failed to retrieve project", "PROJECT_RETRIEVAL_ERROR")
    
    async def update_project(self, project_id: str, project_data: ProjectUpdate, user_id: str) -> ProjectResponse:
        """Update a project"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "projects", project_id):
                raise NotFoundError("Project", project_id)
            
            # Get current project
            project_record = await self._get_project_by_id(project_id)
            if not project_record:
                raise NotFoundError("Project", project_id)
            
            # Validate updates
            if project_data.name is not None:
                await self._validate_project_name(project_data.name)
                # Check if new name conflicts with existing projects
                if (project_data.name != project_record["name"] and 
                    await self._project_name_exists_for_user(project_data.name, user_id)):
                    raise ValidationError(f"Project name '{project_data.name}' already exists")
            
            # Prepare update data
            update_data = {}
            if project_data.name is not None:
                update_data["name"] = project_data.name
            if project_data.description is not None:
                update_data["description"] = project_data.description
            
            if not update_data:
                return ProjectResponse(**project_record)
            
            update_data["updated_at"] = datetime.utcnow()
            
            # Update project in database
            updated_project = await self._update_project_record(project_id, update_data)
            if not updated_project:
                raise ServiceError("Failed to update project", "PROJECT_UPDATE_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="project_update",
                resource_type="projects",
                resource_id=project_id,
                details=update_data
            )
            
            return ProjectResponse(**updated_project)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating project: {e}")
            raise ServiceError("Failed to update project", "PROJECT_UPDATE_ERROR")
    
    async def delete_project(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a project and all its VMs"""
        try:
            # Validate ownership
            if not await self.validate_user_ownership(user_id, "projects", project_id):
                raise NotFoundError("Project", project_id)
            
            project_record = await self._get_project_by_id(project_id)
            if not project_record:
                raise NotFoundError("Project", project_id)
            
            # Get VMs in the project
            project_vms = await self.vm_service.get_user_vms(user_id, project_id=project_id)
            
            # Terminate all VMs in the project
            terminated_vms = 0
            for vm in project_vms:
                if vm.status != "terminated":
                    await self.vm_service.delete_vm(vm.id, user_id)
                    terminated_vms += 1
            
            # Delete the project
            success = await self._delete_project_record(project_id)
            if not success:
                raise ServiceError("Failed to delete project", "PROJECT_DELETE_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="project_delete",
                resource_type="projects",
                resource_id=project_id,
                details={
                    "project_name": project_record["name"],
                    "terminated_vms": terminated_vms
                }
            )
            
            return {
                "success": True,
                "message": f"Project deleted successfully. {terminated_vms} VMs were terminated.",
                "terminated_vms": terminated_vms
            }
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
            raise ServiceError("Failed to delete project", "PROJECT_DELETE_ERROR")
    
    async def health_check(self) -> Dict[str, Any]:
        """Project service health check"""
        try:
            # Test project lookup functionality
            test_result = await self._get_projects_by_user("test-user-id")
            
            return {
                "service": "project",
                "status": "healthy",
                "database_connection": "ok",
                "project_operations": "ok"
            }
        except Exception as e:
            return {
                "service": "project",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_project_creation(self, project_data: ProjectCreate, user_id: str):
        """Validate project creation request"""
        await self._validate_project_name(project_data.name)
        
        # Check project limits
        user_project_count = len(await self._get_projects_by_user(user_id))
        if user_project_count >= 10:  # Max projects per user
            raise ValidationError("Maximum number of projects (10) reached")
    
    async def _validate_project_name(self, name: str):
        """Validate project name"""
        if not name.strip():
            raise ValidationError("Project name cannot be empty")
        
        # Check for reserved names
        reserved_names = ['admin', 'root', 'system', 'api', 'www']
        if name.lower() in reserved_names:
            raise ValidationError(f"Project name '{name}' is reserved")
    
    async def _project_name_exists_for_user(self, name: str, user_id: str) -> bool:
        """Check if project name exists for user"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").select("id").eq("name", name).eq("user_id", user_id).execute()
                return bool(result.data)
            else:
                memory_store = self.db.get_memory_store()
                for project in memory_store["projects"]:
                    if (project.get("name") == name and 
                        project.get("user_id") == user_id):
                        return True
                return False
        except Exception as e:
            self.logger.error(f"Error checking project name existence: {e}")
            return False
    
    async def _create_project_record(self, project_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create project record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").insert(project_record).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                memory_store["projects"].append(project_record)
                return project_record
        except Exception as e:
            self.logger.error(f"Error creating project record: {e}")
            return None
    
    async def _get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").select("*").eq("id", project_id).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                for project in memory_store["projects"]:
                    if project.get("id") == project_id:
                        return project
                return None
        except Exception as e:
            self.logger.error(f"Error getting project by ID: {e}")
            return None
    
    async def _get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get projects by user"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                return result.data or []
            else:
                memory_store = self.db.get_memory_store()
                projects = [project for project in memory_store["projects"] if project.get("user_id") == user_id]
                return sorted(projects, key=lambda x: x.get("created_at", datetime.min), reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting projects by user: {e}")
            return []
    
    async def _update_project_record(self, project_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update project record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").update(update_data).eq("id", project_id).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                for project in memory_store["projects"]:
                    if project.get("id") == project_id:
                        project.update(update_data)
                        return project
                return None
        except Exception as e:
            self.logger.error(f"Error updating project record: {e}")
            return None
    
    async def _delete_project_record(self, project_id: str) -> bool:
        """Delete project record from database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("projects").delete().eq("id", project_id).execute()
                return bool(result.data)
            else:
                memory_store = self.db.get_memory_store()
                original_count = len(memory_store["projects"])
                memory_store["projects"] = [
                    project for project in memory_store["projects"] 
                    if project.get("id") != project_id
                ]
                return len(memory_store["projects"]) < original_count
        except Exception as e:
            self.logger.error(f"Error deleting project record: {e}")
            return False
    
    async def _calculate_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Calculate project statistics"""
        try:
            stats = {
                "vm_count": 0,
                "active_vm_count": 0,
                "total_cost": 0.0
            }
            
            if self.db.get_client():
                supabase = self.db.get_client()
                
                # Count VMs
                vm_result = supabase.table("vms").select("*", count="exact").eq("project_id", project_id).execute()
                stats["vm_count"] = vm_result.count or 0
                
                # Count active VMs
                active_vm_result = supabase.table("vms").select("*", count="exact").eq("project_id", project_id).eq("status", "running").execute()
                stats["active_vm_count"] = active_vm_result.count or 0
                
                # Calculate total cost
                cost_result = supabase.table("vms").select("total_cost").eq("project_id", project_id).execute()
                if cost_result.data:
                    stats["total_cost"] = sum(float(vm.get("total_cost", 0)) for vm in cost_result.data)
            else:
                memory_store = self.db.get_memory_store()
                project_vms = [vm for vm in memory_store["vms"] if vm.get("project_id") == project_id]
                
                stats["vm_count"] = len(project_vms)
                stats["active_vm_count"] = len([vm for vm in project_vms if vm.get("status") == "running"])
                stats["total_cost"] = sum(float(vm.get("total_cost", 0)) for vm in project_vms)
            
            return stats
        except Exception as e:
            self.logger.error(f"Error calculating project stats: {e}")
            return {
                "vm_count": 0,
                "active_vm_count": 0,
                "total_cost": 0.0
            }