# Service Layer Architecture

This document describes the service layer architecture implemented for the Zentry Cloud API backend.

## Overview

The service layer provides a clean separation between business logic and API endpoints, implementing the following principles:

- **Single Responsibility**: Each service handles a specific domain
- **Dependency Injection**: Services are managed through a container
- **Error Handling**: Consistent error handling with custom exceptions
- **Logging & Auditing**: Comprehensive logging and audit trails
- **Testability**: Services are easily testable with mocked dependencies

## Architecture Components

### Base Service (`base_service.py`)

The `BaseService` class provides common functionality for all services:

- **Error Handling**: Custom exception classes (`ServiceError`, `ValidationError`, `NotFoundError`, `InsufficientCreditsError`)
- **Database Access**: Unified database interaction methods
- **Audit Logging**: Automatic audit trail generation
- **Utility Methods**: Common operations like ID generation, credit management

### Service Classes

#### 1. AuthService (`auth_service.py`)
Handles user authentication and profile management:
- User registration with validation
- User login with rate limiting
- Profile updates
- Token refresh functionality

#### 2. VMService (`vm_service.py`)
Manages virtual machine operations:
- VM creation with cost calculation
- VM lifecycle management (start, stop, delete)
- VM status tracking
- Integration with billing service

#### 3. ProjectService (`project_service.py`)
Handles project organization:
- Project creation and management
- Project statistics calculation
- VM organization within projects
- Project deletion with cleanup

#### 4. BillingService (`billing_service.py`)
Manages credits and billing:
- Transaction recording
- Credit management (add/deduct)
- Usage summaries and reporting
- Cost calculations

#### 5. MonitoringService (`monitoring_service.py`)
Handles VM metrics and monitoring:
- Metrics collection and storage
- Performance analytics
- Trend analysis
- Mock data generation for testing

#### 6. UserService (`user_service.py`)
Provides user management functionality:
- User profile management
- Dashboard data aggregation
- Activity logging
- Admin operations

### Service Container (`service_container.py`)

The `ServiceContainer` implements dependency injection:

```python
from services.service_container import service_container

# Initialize services
service_container.initialize()

# Get service instances
auth_service = service_container.get_auth_service()
vm_service = service_container.get_vm_service()
```

## Error Handling

### Custom Exceptions

The service layer uses custom exceptions for better error handling:

```python
# Base service error
class ServiceError(Exception):
    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None)

# Specific error types
class ValidationError(ServiceError)
class NotFoundError(ServiceError)
class InsufficientCreditsError(ServiceError)
```

### Error Mapping

The middleware maps service errors to appropriate HTTP status codes:

- `ValidationError` → 400 Bad Request
- `NotFoundError` → 404 Not Found
- `InsufficientCreditsError` → 400 Bad Request
- `ServiceError` with `PERMISSION_DENIED` → 403 Forbidden
- `ServiceError` with `RATE_LIMITED` → 429 Too Many Requests

## Integration with Routers

Routers are refactored to use services instead of direct database access:

### Before (Direct Database Access)
```python
@router.post("/signup")
async def signup(user_data: UserSignup):
    supabase = db.get_client()
    # Direct database operations
    existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()
    # ... more database code
```

### After (Service Layer)
```python
@router.post("/signup")
async def signup(user_data: UserSignup):
    try:
        auth_service = service_container.get_auth_service()
        return await auth_service.signup(user_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
```

## Benefits

### 1. Separation of Concerns
- Business logic is separated from HTTP handling
- Database access is abstracted
- Validation is centralized

### 2. Testability
- Services can be easily mocked
- Business logic can be tested independently
- Integration tests are more focused

### 3. Reusability
- Services can be used by multiple routers
- Business logic can be shared across different interfaces
- Consistent behavior across the application

### 4. Maintainability
- Changes to business logic are centralized
- Database schema changes are isolated
- Error handling is consistent

### 5. Scalability
- Services can be easily moved to separate processes
- Caching can be added at the service layer
- Performance monitoring is centralized

## Usage Examples

### Creating a VM
```python
# In router
vm_service = service_container.get_vm_service()
try:
    vm = await vm_service.create_vm(vm_data, current_user)
    return vm
except InsufficientCreditsError as e:
    raise HTTPException(status_code=400, detail=e.message)
```

### Recording Metrics
```python
# In monitoring endpoint
monitoring_service = service_container.get_monitoring_service()
try:
    metrics = await monitoring_service.record_vm_metrics(vm_id, metrics_data, user_id)
    return metrics
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=e.message)
```

### Managing Credits
```python
# In billing endpoint
billing_service = service_container.get_billing_service()
try:
    transaction = await billing_service.add_credits(user_id, amount, description)
    return transaction
except ValidationError as e:
    raise HTTPException(status_code=400, detail=e.message)
```

## Testing

The service layer includes comprehensive tests:

- **Unit Tests**: Test individual service methods
- **Integration Tests**: Test service interactions
- **Mock Tests**: Test with mocked dependencies
- **Error Tests**: Test error handling scenarios

Run tests with:
```bash
pytest backend/tests/test_services.py -v
```

## Health Checks

Each service implements a health check method:

```python
# Check all services
health_results = await service_container.health_check_all()

# Check individual service
auth_health = await auth_service.health_check()
```

## Audit Logging

All services automatically log important operations:

```python
await self.log_audit_event(
    user_id=user_id,
    action="vm_create",
    resource_type="vms",
    resource_id=vm_id,
    details={"instance_type": "small", "cost": 0.05}
)
```

## Future Enhancements

### 1. Caching Layer
- Add Redis caching for frequently accessed data
- Implement cache invalidation strategies
- Cache user sessions and permissions

### 2. Event System
- Implement domain events for service communication
- Add event sourcing for audit trails
- Enable real-time notifications

### 3. Service Discovery
- Add service registry for microservices
- Implement health check aggregation
- Enable dynamic service scaling

### 4. Performance Monitoring
- Add service-level metrics
- Implement distributed tracing
- Monitor service dependencies

### 5. Security Enhancements
- Add service-to-service authentication
- Implement rate limiting per service
- Add input sanitization layers

## Migration Guide

To migrate existing routers to use the service layer:

1. **Identify Business Logic**: Extract database operations and business rules
2. **Create Service Methods**: Move logic to appropriate service classes
3. **Update Router**: Replace direct database calls with service calls
4. **Add Error Handling**: Map service errors to HTTP responses
5. **Add Tests**: Create tests for the new service methods
6. **Update Documentation**: Document the new service interface

## Conclusion

The service layer architecture provides a robust foundation for the Zentry Cloud API, enabling better maintainability, testability, and scalability. By separating business logic from HTTP handling and database access, the codebase becomes more modular and easier to evolve.