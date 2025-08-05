#!/usr/bin/env python3
"""
Database initialization script for Zentry Cloud
This script can be run independently to set up the database schema and run migrations
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import db
from database_service import database_service
from migrations.migration_runner import migration_runner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def check_database_connection():
    """Check if database connection is working"""
    logger.info("Checking database connection...")
    
    try:
        health = await db.health_check(force_refresh=True)
        
        if health.status == "healthy":
            logger.info(f"✓ Database connection successful ({health.type})")
            if health.response_time_ms:
                logger.info(f"  Response time: {health.response_time_ms:.2f}ms")
            if health.users_count is not None:
                logger.info(f"  Current users: {health.users_count}")
            return True
        else:
            logger.error(f"✗ Database connection failed: {health.error}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Database connection check failed: {e}")
        return False

async def run_migrations():
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    try:
        # Check for pending migrations first
        pending = await migration_runner.get_pending_migrations()
        
        if not pending:
            logger.info("✓ No pending migrations")
            return True
        
        logger.info(f"Found {len(pending)} pending migrations:")
        for version, _ in pending:
            logger.info(f"  - {version}")
        
        # Run migrations
        success = await migration_runner.run_pending_migrations()
        
        if success:
            logger.info("✓ All migrations completed successfully")
            return True
        else:
            logger.error("✗ Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Migration execution failed: {e}")
        return False

async def verify_schema():
    """Verify database schema integrity"""
    logger.info("Verifying database schema...")
    
    try:
        if settings.use_in_memory_db:
            logger.info("✓ Schema verification skipped for in-memory database")
            return True
        
        # Get database statistics to verify tables exist
        stats = await database_service.get_database_statistics()
        
        if "row_counts" in stats:
            logger.info("✓ Database schema verified")
            logger.info("Table row counts:")
            for table, count in stats["row_counts"].items():
                logger.info(f"  {table}: {count} rows")
            return True
        else:
            logger.warning("⚠ Could not verify schema completely")
            return True
            
    except Exception as e:
        logger.error(f"✗ Schema verification failed: {e}")
        return False

async def optimize_database():
    """Run database optimization"""
    logger.info("Running database optimization...")
    
    try:
        result = await database_service.optimize_database()
        
        if result.get("error"):
            logger.warning(f"⚠ Optimization completed with warnings: {result['error']}")
        else:
            logger.info("✓ Database optimization completed")
            for key, value in result.items():
                if key != "error":
                    logger.info(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database optimization failed: {e}")
        return False

async def main():
    """Main initialization function"""
    logger.info("=== Zentry Cloud Database Initialization ===")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database type: {'In-memory' if settings.use_in_memory_db else 'PostgreSQL'}")
    
    success = True
    
    # Step 1: Check database connection
    if not await check_database_connection():
        logger.error("Database connection failed. Please check your configuration.")
        return False
    
    # Step 2: Run migrations
    if not await run_migrations():
        logger.error("Migration failed. Database may be in an inconsistent state.")
        success = False
    
    # Step 3: Verify schema
    if not await verify_schema():
        logger.error("Schema verification failed.")
        success = False
    
    # Step 4: Optimize database (optional, don't fail on this)
    if not settings.use_in_memory_db:
        await optimize_database()
    
    # Final status
    if success:
        logger.info("=== Database initialization completed successfully ===")
    else:
        logger.error("=== Database initialization completed with errors ===")
    
    # Close database connections
    try:
        await db.close()
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)