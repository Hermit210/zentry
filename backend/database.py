from supabase import create_client, Client
from config import settings
import logging
import asyncpg
from typing import Optional, Dict, Any, List, Union, Tuple
from contextlib import asynccontextmanager
import time
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom database error"""
    pass

class TransactionError(DatabaseError):
    """Transaction-specific error"""
    pass

class ConnectionError(DatabaseError):
    """Database connection error"""
    pass

class MigrationError(DatabaseError):
    """Database migration error"""
    pass

@dataclass
class HealthStatus:
    """Database health status"""
    status: str
    type: str
    connection_count: Optional[int] = None
    users_count: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    last_check: Optional[datetime] = None

@dataclass
class QueryResult:
    """Query execution result"""
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    query: str

class Database:
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.pg_pool: Optional[asyncpg.Pool] = None
        self._connection_retries = 3
        self._connection_timeout = 30
        self._pool_min_size = 5
        self._pool_max_size = 20
        self._query_timeout = 30
        self._health_check_cache: Optional[HealthStatus] = None
        self._health_check_interval = 300  # 5 minutes
        self._connection_metrics = {
            "total_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0.0,
            "last_error": None
        }
        self.in_memory_store: Dict[str, Any] = {
            "users": {},
            "projects": [],
            "vms": [],
            "billing_records": [],
            "vm_metrics": [],
            "audit_logs": [],
            "system_health": []
        }
        self._transaction_lock = asyncio.Lock()
        self.connect()
    
    def connect(self):
        """Initialize database connection based on configuration"""
        try:
            if settings.use_in_memory_db:
                logger.info("Using in-memory database for development")
                return
            
            if settings.supabase_url and settings.supabase_service_key:
                self.supabase = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )
                logger.info("Connected to Supabase successfully")
            elif settings.database_url:
                logger.info("Using direct PostgreSQL connection")
                # Connection pool will be created on first use
            else:
                logger.warning("No database configuration found, falling back to in-memory storage")
                settings.use_in_memory_db = True
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._connection_metrics["last_error"] = str(e)
            if settings.is_production:
                raise ConnectionError(f"Database connection failed: {e}")
            else:
                logger.warning("Falling back to in-memory storage for development")
                settings.use_in_memory_db = True
    
    def get_client(self) -> Optional[Client]:
        """Get Supabase client instance"""
        if settings.use_in_memory_db:
            return None
        
        if not self.supabase and settings.supabase_url:
            self.connect()
        return self.supabase
    
    async def get_pg_connection(self):
        """Get PostgreSQL connection with retry logic"""
        if settings.use_in_memory_db or not settings.database_url:
            return None
        
        for attempt in range(self._connection_retries):
            try:
                if not self.pg_pool:
                    self.pg_pool = await asyncpg.create_pool(
                        settings.database_url,
                        min_size=self._pool_min_size,
                        max_size=self._pool_max_size,
                        command_timeout=self._query_timeout,
                        server_settings={
                            'application_name': 'zentry_cloud_backend',
                            'jit': 'off'  # Disable JIT for better performance on small queries
                        }
                    )
                
                return await self.pg_pool.acquire()
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == self._connection_retries - 1:
                    self._connection_metrics["last_error"] = str(e)
                    raise ConnectionError(f"Failed to acquire database connection after {self._connection_retries} attempts: {e}")
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    def get_memory_store(self) -> Dict[str, Any]:
        """Get in-memory store for development"""
        return self.in_memory_store
    
    async def health_check(self, force_refresh: bool = False) -> HealthStatus:
        """Check database connection health with caching"""
        now = datetime.utcnow()
        
        # Return cached result if still valid
        if (not force_refresh and 
            self._health_check_cache and 
            self._health_check_cache.last_check and
            (now - self._health_check_cache.last_check).total_seconds() < self._health_check_interval):
            return self._health_check_cache
        
        start_time = time.time()
        
        try:
            if settings.use_in_memory_db:
                health = HealthStatus(
                    status="healthy",
                    type="in-memory",
                    users_count=len(self.in_memory_store["users"]),
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=now
                )
            elif self.supabase:
                result = self.supabase.table("users").select("count", count="exact").execute()
                health = HealthStatus(
                    status="healthy",
                    type="supabase",
                    users_count=result.count if result.count is not None else 0,
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=now
                )
            elif settings.database_url:
                conn = await self.get_pg_connection()
                try:
                    # Test basic connectivity and get stats
                    users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                    connection_count = await conn.fetchval(
                        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                    )
                    
                    health = HealthStatus(
                        status="healthy",
                        type="postgresql",
                        users_count=users_count or 0,
                        connection_count=connection_count,
                        response_time_ms=(time.time() - start_time) * 1000,
                        last_check=now
                    )
                finally:
                    if conn:
                        await self.pg_pool.release(conn)
            else:
                health = HealthStatus(
                    status="unhealthy",
                    type="unknown",
                    error="No database connection available",
                    last_check=now
                )
            
            # Cache the result
            self._health_check_cache = health
            
            # Record health status in database if possible
            if health.status == "healthy" and not settings.use_in_memory_db:
                await self._record_system_health("database", health.status, None, {
                    "response_time_ms": health.response_time_ms,
                    "connection_count": health.connection_count,
                    "users_count": health.users_count
                })
            
            return health
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health = HealthStatus(
                status="unhealthy",
                type="unknown",
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=now
            )
            self._health_check_cache = health
            self._connection_metrics["last_error"] = str(e)
            return health
    
    async def run_migrations(self) -> bool:
        """Run database migrations if needed"""
        if settings.use_in_memory_db:
            logger.info("Skipping migrations for in-memory database")
            return True
        
        try:
            from migrations.migration_runner import migration_runner
            success = await migration_runner.run_pending_migrations()
            
            if success:
                await self._record_system_health("migrations", "healthy", "All migrations completed successfully")
            else:
                await self._record_system_health("migrations", "critical", "Migration failed")
            
            return success
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self._record_system_health("migrations", "critical", f"Migration error: {str(e)}")
            raise MigrationError(f"Migration failed: {e}")
    
    @asynccontextmanager
    async def transaction(self):
        """Database transaction context manager"""
        if settings.use_in_memory_db:
            # For in-memory database, we don't have real transactions
            # but we can simulate with a lock
            async with self._transaction_lock:
                yield None
            return
        
        conn = None
        transaction = None
        
        try:
            conn = await self.get_pg_connection()
            transaction = conn.transaction()
            await transaction.start()
            
            yield conn
            
            await transaction.commit()
            
        except Exception as e:
            if transaction:
                await transaction.rollback()
            logger.error(f"Transaction failed: {e}")
            raise TransactionError(f"Transaction failed: {e}")
        finally:
            if conn:
                await self.pg_pool.release(conn)
    
    async def execute_query(self, query: str, params: Optional[Union[List, Dict]] = None, fetch_mode: str = "all") -> QueryResult:
        """Execute a database query with metrics tracking"""
        start_time = time.time()
        
        try:
            if settings.use_in_memory_db:
                # For in-memory database, we can't execute arbitrary SQL
                # This would need to be implemented based on specific needs
                return QueryResult(
                    rows=[],
                    row_count=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    query=query
                )
            
            conn = await self.get_pg_connection()
            try:
                if fetch_mode == "all":
                    if params:
                        rows = await conn.fetch(query, *params if isinstance(params, list) else params)
                    else:
                        rows = await conn.fetch(query)
                    result_rows = [dict(row) for row in rows]
                elif fetch_mode == "one":
                    if params:
                        row = await conn.fetchrow(query, *params if isinstance(params, list) else params)
                    else:
                        row = await conn.fetchrow(query)
                    result_rows = [dict(row)] if row else []
                elif fetch_mode == "val":
                    if params:
                        val = await conn.fetchval(query, *params if isinstance(params, list) else params)
                    else:
                        val = await conn.fetchval(query)
                    result_rows = [{"value": val}] if val is not None else []
                else:
                    # Execute without fetching (for INSERT, UPDATE, DELETE)
                    if params:
                        result = await conn.execute(query, *params if isinstance(params, list) else params)
                    else:
                        result = await conn.execute(query)
                    result_rows = []
                
                execution_time = (time.time() - start_time) * 1000
                
                # Update metrics
                self._connection_metrics["total_queries"] += 1
                self._connection_metrics["avg_response_time"] = (
                    (self._connection_metrics["avg_response_time"] * (self._connection_metrics["total_queries"] - 1) + execution_time) /
                    self._connection_metrics["total_queries"]
                )
                
                return QueryResult(
                    rows=result_rows,
                    row_count=len(result_rows),
                    execution_time_ms=execution_time,
                    query=query
                )
                
            finally:
                await self.pg_pool.release(conn)
                
        except Exception as e:
            self._connection_metrics["failed_queries"] += 1
            self._connection_metrics["last_error"] = str(e)
            logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def get_connection_metrics(self) -> Dict[str, Any]:
        """Get database connection metrics"""
        metrics = self._connection_metrics.copy()
        
        if self.pg_pool:
            metrics.update({
                "pool_size": self.pg_pool.get_size(),
                "pool_min_size": self.pg_pool.get_min_size(),
                "pool_max_size": self.pg_pool.get_max_size(),
                "pool_idle_connections": self.pg_pool.get_idle_size()
            })
        
        return metrics
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        if settings.use_in_memory_db:
            return {"status": "skipped", "reason": "in-memory database"}
        
        results = {}
        
        try:
            # Refresh materialized views
            await self.execute_query("SELECT refresh_user_stats()", fetch_mode="execute")
            results["materialized_views"] = "refreshed"
            
            # Update table statistics
            await self.execute_query("ANALYZE", fetch_mode="execute")
            results["statistics"] = "updated"
            
            # Clean up old audit logs (keep 90 days)
            cleanup_result = await self.execute_query("SELECT cleanup_old_audit_logs(90)", fetch_mode="val")
            results["cleanup"] = f"removed {cleanup_result} old records"
            
            logger.info("Database optimization completed successfully")
            await self._record_system_health("optimization", "healthy", "Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            results["error"] = str(e)
            await self._record_system_health("optimization", "warning", f"Optimization failed: {str(e)}")
        
        return results
    
    async def _record_system_health(self, component: str, status: str, message: Optional[str] = None, metrics: Optional[Dict] = None):
        """Record system health status"""
        try:
            if settings.use_in_memory_db:
                self.in_memory_store["system_health"].append({
                    "component": component,
                    "status": status,
                    "message": message,
                    "metrics": metrics,
                    "checked_at": datetime.utcnow().isoformat()
                })
            else:
                await self.execute_query(
                    "SELECT record_system_health($1, $2, $3, $4)",
                    [component, status, message, json.dumps(metrics) if metrics else None],
                    fetch_mode="execute"
                )
        except Exception as e:
            logger.warning(f"Failed to record system health: {e}")
    
    async def close(self):
        """Close database connections"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("Database connection pool closed")

# Global database instance
db = Database()