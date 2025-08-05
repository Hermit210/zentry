# Database Enhancements Documentation

This document describes the comprehensive database enhancements implemented for the Zentry Cloud backend, including schema management, health monitoring, transaction support, and optimization features.

## Overview

The database enhancements provide:

1. **Comprehensive Migration System** - Versioned database migrations with rollback support
2. **Health Monitoring** - Real-time database health checks and metrics
3. **Transaction Support** - Robust transaction management with error handling
4. **Query Optimization** - Database indexing and performance optimizations
5. **Audit Logging** - Complete audit trail for system events
6. **Connection Management** - Advanced connection pooling and retry logic
7. **Data Cleanup** - Automated data retention and cleanup policies

## Architecture

### Core Components

1. **Database Class** (`database.py`)
   - Enhanced connection management with retry logic
   - Health monitoring with caching
   - Transaction context manager
   - Query execution with metrics tracking
   - Connection pooling for PostgreSQL

2. **DatabaseService Class** (`database_service.py`)
   - High-level database operations
   - Audit logging functionality
   - System health tracking
   - Data cleanup and optimization

3. **Migration Runner** (`migrations/migration_runner.py`)
   - Versioned migration execution
   - Schema integrity verification
   - Rollback support
   - Error handling and logging

4. **Health Monitoring** (`routers/health.py`)
   - REST API endpoints for health checks
   - Database statistics and metrics
   - System monitoring dashboard

## Database Schema

### Core Tables

- **users** - User accounts with credits and spending tracking
- **projects** - Project organization for VMs
- **vms** - Virtual machine instances with status tracking
- **billing_records** - Detailed billing and usage records
- **vm_metrics** - Performance metrics for VMs

### Audit and Monitoring Tables

- **audit_logs** - Complete audit trail of system events
- **system_health** - System health monitoring records
- **vm_state_transitions** - VM status change tracking
- **connection_metrics** - Database connection performance metrics

### Migration Tracking

- **schema_migrations** - Tracks applied database migrations

## Migration System

### Migration Files

Migrations are stored in `backend/migrations/` with the following naming convention:
- `001_initial_schema.sql` - Initial database schema
- `002_add_indexes_and_constraints.sql` - Performance optimizations
- `003_add_audit_and_logging.sql` - Audit and monitoring tables

### Running Migrations

```bash
# Run all pending migrations
python init_database.py

# Or programmatically
from migrations.migration_runner import migration_runner
await migration_runner.run_pending_migrations()
```

### Migration Features

- **Transactional** - Each migration runs in a transaction
- **Versioned** - Tracks which migrations have been applied
- **Rollback Support** - Can rollback migrations with rollback scripts
- **Schema Verification** - Verifies schema integrity after migrations
- **Error Handling** - Comprehensive error reporting and logging

## Health Monitoring

### Health Check Endpoints

- `GET /health/` - Basic health status
- `GET /health/database` - Detailed database health
- `GET /health/database/statistics` - Database statistics
- `GET /health/system` - System health history

### Health Metrics

- **Connection Status** - Database connectivity
- **Response Time** - Query response times
- **Connection Count** - Active database connections
- **Table Statistics** - Row counts and table sizes
- **Error Tracking** - Failed queries and connection errors

### Caching

Health checks are cached for 5 minutes to reduce database load while providing timely status updates.

## Transaction Support

### Usage

```python
from database import db

# Using transaction context manager
async with db.transaction() as conn:
    # Perform database operations
    await conn.execute("INSERT INTO users ...")
    await conn.execute("UPDATE projects ...")
    # Automatically commits on success, rolls back on error
```

### Features

- **Automatic Rollback** - Rolls back on any exception
- **Connection Management** - Handles connection acquisition and release
- **Error Handling** - Comprehensive error reporting
- **Async Support** - Full async/await support

## Query Optimization

### Indexes

The system includes comprehensive indexing for:

- **Primary Keys** - All tables have UUID primary keys
- **Foreign Keys** - All relationships are indexed
- **Query Patterns** - Common query patterns are optimized
- **Partial Indexes** - Indexes on filtered data (e.g., active users)
- **Composite Indexes** - Multi-column indexes for complex queries

### Performance Features

- **Connection Pooling** - Efficient connection reuse
- **Query Metrics** - Tracks query performance
- **Materialized Views** - Pre-computed user statistics
- **Database Functions** - Server-side logic for complex operations

## Audit Logging

### Audit Events

The system logs:
- User authentication events
- Resource creation/modification/deletion
- Administrative actions
- System configuration changes
- Error events

### Audit Data

Each audit log includes:
- User ID (if applicable)
- Action performed
- Resource type and ID
- Old and new values
- IP address and user agent
- Timestamp

### Usage

```python
from database_service import database_service

await database_service.log_audit_event(
    user_id="user-123",
    action="vm_created",
    resource_type="vm",
    resource_id="vm-456",
    new_values={"name": "my-vm", "instance_type": "small"}
)
```

## Data Cleanup

### Retention Policies

- **Audit Logs** - 90 days (configurable)
- **System Health** - 45 days
- **Connection Metrics** - 30 days
- **VM Metrics** - 60 days

### Cleanup Functions

```python
# Clean up old data
result = await database_service.cleanup_old_data(retention_days=90)

# Database optimization
result = await database_service.optimize_database()
```

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Development Mode
USE_IN_MEMORY_DB=true  # For development/testing
ENVIRONMENT=development

# Connection Settings
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
DB_QUERY_TIMEOUT=30
```

### Database Types

1. **PostgreSQL** - Production database with full features
2. **Supabase** - Managed PostgreSQL with additional features
3. **In-Memory** - Development/testing with simulated operations

## API Endpoints

### Health Monitoring

- `GET /health/` - Basic health check
- `GET /health/database` - Database health details
- `GET /health/database/statistics` - Database statistics
- `POST /health/database/optimize` - Run optimization
- `POST /health/database/migrations` - Run migrations
- `GET /health/system` - System health history
- `GET /health/audit` - User audit logs
- `POST /health/cleanup` - Clean up old data

### Authentication

Most health endpoints require authentication. Admin-level operations require appropriate permissions.

## Error Handling

### Error Types

- **DatabaseError** - General database errors
- **ConnectionError** - Connection-related errors
- **TransactionError** - Transaction-specific errors
- **MigrationError** - Migration-related errors

### Error Recovery

- **Connection Retry** - Automatic retry with exponential backoff
- **Transaction Rollback** - Automatic rollback on errors
- **Graceful Degradation** - Fallback to in-memory storage in development
- **Error Logging** - Comprehensive error logging and tracking

## Testing

### Test Suite

Run the test suite to verify all enhancements:

```bash
python test_database_enhancements.py
```

### Test Coverage

- Health check functionality
- Transaction support
- Audit logging
- Data cleanup
- Connection metrics
- Error handling

## Performance Considerations

### Optimization Features

- **Connection Pooling** - Reuses database connections
- **Query Caching** - Caches health check results
- **Materialized Views** - Pre-computed statistics
- **Efficient Indexing** - Optimized for common queries
- **Batch Operations** - Bulk data operations where possible

### Monitoring

- Query execution times
- Connection pool utilization
- Error rates and types
- Database response times
- Resource utilization

## Security

### Security Features

- **SQL Injection Prevention** - Parameterized queries
- **Connection Security** - Encrypted connections
- **Audit Trail** - Complete audit logging
- **Access Control** - Authentication required for admin operations
- **Data Validation** - Input validation and sanitization

### Best Practices

- Use parameterized queries
- Validate all inputs
- Log security events
- Monitor for suspicious activity
- Regular security updates

## Deployment

### Production Deployment

1. Set up PostgreSQL database
2. Configure environment variables
3. Run database initialization
4. Verify health checks
5. Monitor system performance

### Development Setup

1. Set `USE_IN_MEMORY_DB=true`
2. Run test suite
3. Verify functionality
4. Test with real database when ready

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check database URL and credentials
   - Verify network connectivity
   - Check connection pool settings

2. **Migration Failures**
   - Check migration file syntax
   - Verify database permissions
   - Review migration logs

3. **Performance Issues**
   - Check connection pool utilization
   - Review query performance
   - Optimize indexes if needed

### Debugging

- Enable debug logging
- Check health endpoints
- Review audit logs
- Monitor connection metrics
- Use database profiling tools

## Future Enhancements

### Planned Features

- **Read Replicas** - Support for read-only replicas
- **Sharding** - Horizontal scaling support
- **Advanced Monitoring** - More detailed metrics
- **Automated Backups** - Scheduled backup system
- **Performance Analytics** - Query performance analysis

### Extensibility

The system is designed to be extensible:
- Add new migration files
- Extend audit logging
- Add custom health checks
- Implement additional optimizations
- Add new monitoring metrics