from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging
import sys

# Import configuration and database
from config import settings
from database import db
from models import HealthCheck

# Import routers
from routers import auth, projects, vms, health, api_version, billing, monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application with comprehensive documentation
app = FastAPI(
    title="Zentry Cloud API",
    description="""
    ## Developer-first cloud platform API
    
    This comprehensive API provides cloud infrastructure management capabilities including:
    
    * **🔐 Authentication** - Secure user registration, login, and JWT token management
    * **📁 Project Management** - Organize resources into projects with full CRUD operations
    * **🖥️ Virtual Machine Management** - Complete VM lifecycle management with real-time monitoring
    * **💳 Billing & Credits** - Transparent usage tracking and credit management system
    * **📊 Monitoring** - Real-time VM metrics, system health, and performance analytics
    * **🔧 System Administration** - Health checks, database management, and audit logging
    
    ### Getting Started
    
    1. **Register** for an account using `/auth/signup` (includes 50 welcome credits)
    2. **Login** to obtain your JWT access token via `/auth/login`
    3. **Create a project** to organize your resources at `/projects`
    4. **Deploy VMs** within your projects using `/vms`
    5. **Monitor** your infrastructure with comprehensive metrics endpoints
    
    ### Authentication & Security
    
    Most endpoints require authentication. Include your JWT token in the Authorization header:
    ```
    Authorization: Bearer your_jwt_token_here
    ```
    
    **Security Features:**
    - JWT tokens with configurable expiration
    - Secure password hashing with bcrypt
    - Rate limiting on sensitive endpoints
    - Input validation and sanitization
    - Audit logging for all operations
    
    ### API Versioning
    
    This API follows semantic versioning. Current version: **v1.0.0**
    
    - **Major versions** (1.x.x): Breaking changes
    - **Minor versions** (x.1.x): New features, backwards compatible
    - **Patch versions** (x.x.1): Bug fixes, backwards compatible
    
    ### Rate Limits
    
    - **Authentication endpoints**: 5 requests per minute per IP
    - **VM operations**: 10 requests per minute per user
    - **General API**: 100 requests per minute per user
    - **Admin endpoints**: 20 requests per minute per user
    
    ### Error Handling
    
    All errors follow a consistent format with appropriate HTTP status codes:
    - **400**: Bad Request (validation errors)
    - **401**: Unauthorized (authentication required)
    - **403**: Forbidden (insufficient permissions)
    - **404**: Not Found (resource doesn't exist)
    - **409**: Conflict (resource already exists)
    - **429**: Too Many Requests (rate limit exceeded)
    - **500**: Internal Server Error (server issues)
    
    ### Support & Resources
    
    - **Interactive Documentation**: Available at `/docs` (Swagger UI)
    - **Alternative Documentation**: Available at `/redoc` (ReDoc)
    - **OpenAPI Schema**: Available at `/openapi.json`
    - **Health Status**: Monitor API health at `/health`
    - **System Status**: Check system metrics at `/health/system`
    
    For additional support, please contact our development team.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Zentry Cloud API Support",
        "email": "api-support@zentrycloud.com",
        "url": "https://docs.zentrycloud.com/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api-staging.zentrycloud.com",
            "description": "Staging server"
        },
        {
            "url": "https://api.zentrycloud.com",
            "description": "Production server"
        }
    ],
    openapi_tags=[
        {
            "name": "System",
            "description": "System information, health checks, and API status endpoints"
        },
        {
            "name": "Authentication", 
            "description": "User authentication, registration, and profile management"
        },
        {
            "name": "Projects",
            "description": "Project management for organizing cloud resources"
        },
        {
            "name": "Virtual Machines",
            "description": "Complete VM lifecycle management and operations"
        },
        {
            "name": "Monitoring",
            "description": "VM metrics, system monitoring, and performance analytics"
        },
        {
            "name": "Billing",
            "description": "Credit management, usage tracking, and billing operations"
        },
        {
            "name": "Health",
            "description": "System health monitoring, database status, and diagnostics"
        },
        {
            "name": "API Versioning",
            "description": "API version management, compatibility checking, and changelog information"
        }
    ]
)

# Add security scheme for JWT authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,  # Include the tags
        contact=app.contact,
        license_info=app.license_info,
        servers=app.servers,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication. Include your token in the Authorization header as 'Bearer <token>'"
        }
    }
    
    # Add security to protected endpoints
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # Add security to endpoints that typically require auth (except public ones)
                if not any(tag in operation.get("tags", []) for tag in ["System", "API Versioning"]) or "auth" in path:
                    if path not in ["/", "/health", "/health-simple", "/vms/pricing/info", "/api/version", "/api/versions", "/api/compatibility", "/api/changelog"]:
                        operation["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_version.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(vms.router)
app.include_router(billing.router)
app.include_router(monitoring.router)
app.include_router(health.router)

# Root endpoint with comprehensive API information
@app.get("/", 
         tags=["System"],
         summary="API Root Information",
         description="Get comprehensive API information, status, and available endpoints",
         response_description="API information including version, status, and navigation links",
         responses={
             200: {
                 "description": "API information retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "message": "Zentry Cloud API",
                             "version": "1.0.0",
                             "status": "running",
                             "environment": "development",
                             "api_info": {
                                 "title": "Zentry Cloud API",
                                 "description": "Developer-first cloud platform API",
                                 "contact": "api-support@zentrycloud.com"
                             },
                             "endpoints": {
                                 "documentation": "/docs",
                                 "alternative_docs": "/redoc", 
                                 "openapi_schema": "/openapi.json",
                                 "health_check": "/health",
                                 "authentication": "/auth",
                                 "projects": "/projects",
                                 "virtual_machines": "/vms"
                             },
                             "features": [
                                 "JWT Authentication",
                                 "Project Management", 
                                 "VM Lifecycle Management",
                                 "Real-time Monitoring",
                                 "Credit-based Billing",
                                 "Comprehensive API Documentation"
                             ],
                             "rate_limits": {
                                 "authentication": "5 requests/minute",
                                 "vm_operations": "10 requests/minute", 
                                 "general_api": "100 requests/minute"
                             },
                             "timestamp": "2024-01-15T10:30:00Z"
                         }
                     }
                 }
             }
         })
async def root():
    """
    Get comprehensive API information and status.
    
    This endpoint provides:
    - API version and status information
    - Available endpoint categories
    - Feature overview
    - Rate limiting information
    - Navigation links to documentation
    
    **No authentication required** - This is a public endpoint for API discovery.
    """
    return {
        "message": "Zentry Cloud API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "api_info": {
            "title": "Zentry Cloud API",
            "description": "Developer-first cloud platform API",
            "contact": "api-support@zentrycloud.com"
        },
        "endpoints": {
            "documentation": "/docs",
            "alternative_docs": "/redoc",
            "openapi_schema": "/openapi.json", 
            "health_check": "/health",
            "authentication": "/auth",
            "projects": "/projects",
            "virtual_machines": "/vms"
        },
        "features": [
            "JWT Authentication",
            "Project Management",
            "VM Lifecycle Management", 
            "Real-time Monitoring",
            "Credit-based Billing",
            "Comprehensive API Documentation"
        ],
        "rate_limits": {
            "authentication": "5 requests/minute",
            "vm_operations": "10 requests/minute",
            "general_api": "100 requests/minute"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Basic health check endpoint (kept for backward compatibility)
@app.get("/health-simple", 
         response_model=HealthCheck, 
         tags=["System"],
         summary="Simple Health Check",
         description="Basic health check endpoint for load balancers and monitoring systems",
         response_description="Simple health status with database connectivity",
         responses={
             200: {
                 "description": "Health check completed successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "status": "healthy",
                             "timestamp": "2024-01-15T10:30:00Z",
                             "environment": "development",
                             "database": {
                                 "status": "healthy",
                                 "type": "postgresql",
                                 "error": None
                             },
                             "version": "1.0.0"
                         }
                     }
                 }
             },
             503: {
                 "description": "Service unavailable - health check failed",
                 "content": {
                     "application/json": {
                         "example": {
                             "status": "unhealthy",
                             "timestamp": "2024-01-15T10:30:00Z",
                             "environment": "development",
                             "database": {
                                 "status": "unhealthy",
                                 "error": "Connection timeout"
                             }
                         }
                     }
                 }
             }
         })
async def simple_health_check():
    """
    Simple health check endpoint for monitoring and load balancers.
    
    This endpoint provides:
    - Overall system health status
    - Database connectivity status
    - Environment information
    - Timestamp of the check
    
    **Use this endpoint for:**
    - Load balancer health checks
    - Monitoring system integration
    - Quick system status verification
    
    **No authentication required** - This is a public monitoring endpoint.
    """
    try:
        # Check database connection
        db_health = await db.health_check()
        
        return HealthCheck(
            status="healthy" if db_health.status == "healthy" else "unhealthy",
            timestamp=datetime.utcnow(),
            environment=settings.environment,
            database={
                "status": db_health.status,
                "type": db_health.type,
                "error": db_health.error
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            environment=settings.environment,
            database={"status": "unhealthy", "error": str(e)}
        )

# Add error handlers
from middleware.error_handler import exception_handlers
for exc_type, handler in exception_handlers.items():
    app.add_exception_handler(exc_type, handler)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Zentry Cloud API in {settings.environment} mode")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    
    # Initialize service container
    try:
        from services.service_container import service_container
        service_container.initialize()
        logger.info("Service container initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service container: {e}")
    
    # Test database connection
    try:
        health = await db.health_check()
        if health.status == "healthy":
            logger.info(f"Database connection successful ({health.type})")
            
            # Run database migrations
            migration_success = await db.run_migrations()
            if migration_success:
                logger.info("Database migrations completed successfully")
            else:
                logger.warning("Database migrations failed or were skipped")
        else:
            logger.warning(f"Database connection issue: {health.error}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Zentry Cloud API")
    
    # Close database connections
    try:
        await db.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level="info" if settings.debug else "warning"
    )