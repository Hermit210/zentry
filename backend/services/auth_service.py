from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from models import UserSignup, UserLogin, UserUpdate, Token, UserResponse, UserRole
from .base_service import BaseService, ServiceError, ValidationError, NotFoundError
from auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    check_rate_limit, record_failed_login, clear_failed_login
)
from config import settings
import re

class AuthService(BaseService):
    """Authentication service handling user registration, login, and profile management"""
    
    async def signup(self, user_data: UserSignup) -> Token:
        """Register a new user account"""
        try:
            # Validate input
            await self._validate_signup_data(user_data)
            
            # Check if user already exists
            if await self._user_exists(user_data.email):
                raise ValidationError("Email already registered")
            
            # Hash password and create user record
            hashed_password = get_password_hash(user_data.password)
            
            user_record = {
                "id": self.generate_id(),
                "email": user_data.email,
                "name": user_data.name,
                "hashed_password": hashed_password,
                "credits": 50.0,  # Welcome credits
                "total_spent": 0.0,
                "vm_count": 0,
                "project_count": 0,
                "active_vm_count": 0,
                "is_active": True,
                "role": UserRole.USER.value,
                "created_at": datetime.utcnow(),
                "updated_at": None,
                "last_login": None
            }
            
            # Save user to database
            created_user = await self._create_user(user_record)
            if not created_user:
                raise ServiceError("Failed to create user account", "USER_CREATION_FAILED")
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = create_access_token(
                data={"sub": created_user["email"]}, 
                expires_delta=access_token_expires
            )
            
            # Log audit event
            await self.log_audit_event(
                user_id=created_user["id"],
                action="user_signup",
                resource_type="users",
                resource_id=created_user["id"],
                details={"email": user_data.email, "name": user_data.name}
            )
            
            user_response = UserResponse(**created_user)
            
            return Token(
                access_token=access_token,
                expires_in=settings.access_token_expire_minutes * 60,
                user=user_response
            )
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Signup error: {e}")
            raise ServiceError("Internal server error during signup", "SIGNUP_ERROR")
    
    async def login(self, user_data: UserLogin) -> Token:
        """Authenticate user and return access token"""
        try:
            # Check rate limiting
            if not check_rate_limit(user_data.email):
                raise ServiceError(
                    "Too many failed login attempts. Please try again later.",
                    "RATE_LIMITED"
                )
            
            # Get user from database
            user_record = await self._get_user_by_email(user_data.email)
            if not user_record:
                record_failed_login(user_data.email)
                raise ValidationError("Invalid email or password")
            
            # Verify password
            if not verify_password(user_data.password, user_record["hashed_password"]):
                record_failed_login(user_data.email)
                raise ValidationError("Invalid email or password")
            
            # Check if user is active
            if not user_record.get("is_active", True):
                raise ServiceError("User account is deactivated", "ACCOUNT_DEACTIVATED")
            
            # Clear failed login attempts
            clear_failed_login(user_data.email)
            
            # Update last login timestamp
            await self._update_last_login(user_record["id"])
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = create_access_token(
                data={"sub": user_record["email"]}, 
                expires_delta=access_token_expires
            )
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_record["id"],
                action="user_login",
                resource_type="users",
                resource_id=user_record["id"],
                details={"email": user_data.email}
            )
            
            user_response = UserResponse(**user_record)
            
            return Token(
                access_token=access_token,
                expires_in=settings.access_token_expire_minutes * 60,
                user=user_response
            )
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            raise ServiceError("Internal server error during login", "LOGIN_ERROR")
    
    async def get_user_profile(self, user_id: str) -> UserResponse:
        """Get user profile with updated statistics"""
        try:
            user_record = await self._get_user_by_id(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Update user statistics
            stats = await self._calculate_user_stats(user_id)
            user_record.update(stats)
            
            return UserResponse(**user_record)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            raise ServiceError("Failed to retrieve user profile", "PROFILE_ERROR")
    
    async def update_user_profile(self, user_id: str, updates: UserUpdate) -> UserResponse:
        """Update user profile information"""
        try:
            # Validate updates
            if updates.name is not None:
                await self._validate_name(updates.name)
            
            # Get current user
            user_record = await self._get_user_by_id(user_id)
            if not user_record:
                raise NotFoundError("User", user_id)
            
            # Prepare update data
            update_data = {}
            if updates.name is not None:
                update_data["name"] = updates.name
            
            if not update_data:
                return UserResponse(**user_record)
            
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user in database
            updated_user = await self._update_user(user_id, update_data)
            if not updated_user:
                raise ServiceError("Failed to update user profile", "UPDATE_FAILED")
            
            # Log audit event
            await self.log_audit_event(
                user_id=user_id,
                action="profile_update",
                resource_type="users",
                resource_id=user_id,
                details=update_data
            )
            
            return UserResponse(**updated_user)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            raise ServiceError("Failed to update user profile", "UPDATE_ERROR")
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        try:
            from auth import refresh_access_token
            return await refresh_access_token(refresh_token)
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Authentication service health check"""
        try:
            # Test user lookup functionality
            test_result = await self._get_user_by_email("test@example.com")
            
            return {
                "service": "auth",
                "status": "healthy",
                "database_connection": "ok",
                "password_hashing": "ok",
                "token_generation": "ok"
            }
        except Exception as e:
            return {
                "service": "auth",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_signup_data(self, user_data: UserSignup):
        """Validate signup data"""
        # Email validation (already handled by EmailStr)
        
        # Name validation
        await self._validate_name(user_data.name)
        
        # Password validation
        if len(user_data.password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Za-z]', user_data.password):
            raise ValidationError("Password must contain at least one letter")
        
        if not re.search(r'\d', user_data.password):
            raise ValidationError("Password must contain at least one number")
    
    async def _validate_name(self, name: str):
        """Validate user name"""
        if not name.strip():
            raise ValidationError("Name cannot be empty")
        
        if not re.match(r"^[a-zA-Z\s\-']+$", name.strip()):
            raise ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes")
    
    async def _user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        user = await self._get_user_by_email(email)
        return user is not None
    
    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").select("*").eq("email", email).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                return memory_store["users"].get(email)
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            return None
    
    async def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
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
            self.logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def _create_user(self, user_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create user in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("users").insert(user_record).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                memory_store["users"][user_record["email"]] = user_record
                return user_record
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return None
    
    async def _update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user in database"""
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
            self.logger.error(f"Error updating user: {e}")
            return None
    
    async def _update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            await self._update_user(user_id, {"last_login": datetime.utcnow()})
        except Exception as e:
            self.logger.warning(f"Failed to update last login for user {user_id}: {e}")
    
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