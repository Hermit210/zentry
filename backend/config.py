from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Database Configuration (fallback for direct PostgreSQL)
    database_url: Optional[str] = None
    
    # JWT Configuration
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Environment Configuration
    environment: str = "development"
    debug: bool = True
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Development Mode Settings
    use_in_memory_db: bool = False
    enable_demo_mode: bool = False
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            logger.warning("SECRET_KEY should be at least 32 characters long for security")
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production', 'test']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def has_database_config(self) -> bool:
        """Check if we have either Supabase or direct database configuration"""
        return bool(
            (self.supabase_url and self.supabase_service_key) or 
            self.database_url or 
            self.use_in_memory_db
        )
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present"""
        errors = []
        
        # Check database configuration
        if not self.has_database_config:
            if self.is_production:
                errors.append("Production environment requires database configuration (Supabase or DATABASE_URL)")
            else:
                logger.warning("No database configuration found, falling back to in-memory storage")
                self.use_in_memory_db = True
        
        # Check JWT secret in production
        if self.is_production and len(self.secret_key) < 32:
            errors.append("Production environment requires a secure SECRET_KEY (min 32 characters)")
        
        # Check Supabase configuration completeness
        if self.supabase_url and not self.supabase_service_key:
            errors.append("SUPABASE_URL provided but SUPABASE_SERVICE_KEY is missing")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

def get_settings() -> Settings:
    """Get validated settings instance"""
    settings = Settings()
    
    if not settings.validate_configuration():
        if settings.is_production:
            raise ValueError("Invalid configuration for production environment")
        else:
            logger.warning("Configuration issues detected, but continuing in development mode")
    
    return settings

# Global settings instance
settings = get_settings()