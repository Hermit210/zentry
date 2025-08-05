#!/usr/bin/env python3
"""
Test script for database enhancements
This script tests the database operations without requiring all dependencies
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for testing
os.environ["USE_IN_MEMORY_DB"] = "true"
os.environ["ENVIRONMENT"] = "development"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_database_operations():
    """Test database operations with in-memory database"""
    logger.info("=== Testing Database Enhancements ===")
    
    try:
        # Import after setting environment variables
        from config import settings
        from database import db
        from database_service import database_service
        
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Using in-memory database: {settings.use_in_memory_db}")
        
        # Test 1: Health check
        logger.info("\n1. Testing health check...")
        health = await db.health_check()
        logger.info(f"Health status: {health.status}")
        logger.info(f"Database type: {health.type}")
        if health.response_time_ms:
            logger.info(f"Response time: {health.response_time_ms:.2f}ms")
        
        # Test 2: Database service health check
        logger.info("\n2. Testing database service health check...")
        service_health = await database_service.health_check()
        logger.info(f"Service health: {service_health}")
        
        # Test 3: Connection metrics
        logger.info("\n3. Testing connection metrics...")
        metrics = await db.get_connection_metrics()
        logger.info(f"Connection metrics: {metrics}")
        
        # Test 4: Database statistics
        logger.info("\n4. Testing database statistics...")
        stats = await database_service.get_database_statistics()
        logger.info(f"Database statistics: {stats}")
        
        # Test 5: Audit logging
        logger.info("\n5. Testing audit logging...")
        audit_success = await database_service.log_audit_event(
            user_id="test-user-123",
            action="test_action",
            resource_type="test_resource",
            resource_id="test-resource-123",
            new_values={"test": "value"}
        )
        logger.info(f"Audit log success: {audit_success}")
        
        # Test 6: Get audit logs
        logger.info("\n6. Testing audit log retrieval...")
        audit_logs = await database_service.get_audit_logs(limit=10)
        logger.info(f"Retrieved {len(audit_logs)} audit logs")
        
        # Test 7: System health recording
        logger.info("\n7. Testing system health recording...")
        await db._record_system_health("test_component", "healthy", "Test message", {"test_metric": 100})
        
        # Test 8: System health history
        logger.info("\n8. Testing system health history...")
        health_history = await database_service.get_system_health_history(hours=1)
        logger.info(f"Retrieved {len(health_history)} health records")
        
        # Test 9: Data cleanup
        logger.info("\n9. Testing data cleanup...")
        cleanup_result = await database_service.cleanup_old_data(retention_days=30)
        logger.info(f"Cleanup result: {cleanup_result}")
        
        # Test 10: Database optimization
        logger.info("\n10. Testing database optimization...")
        optimization_result = await database_service.optimize_database()
        logger.info(f"Optimization result: {optimization_result}")
        
        logger.info("\n=== All tests completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_transaction_support():
    """Test transaction support"""
    logger.info("\n=== Testing Transaction Support ===")
    
    try:
        from database import db
        
        # Test transaction context manager
        async with db.transaction() as conn:
            logger.info("Transaction started successfully")
            # In a real scenario, we would perform database operations here
            logger.info("Transaction operations would be performed here")
        
        logger.info("Transaction completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Transaction test failed: {e}")
        return False

async def main():
    """Main test function"""
    success = True
    
    # Test basic database operations
    if not await test_database_operations():
        success = False
    
    # Test transaction support
    if not await test_transaction_support():
        success = False
    
    if success:
        logger.info("\n🎉 All database enhancement tests passed!")
    else:
        logger.error("\n❌ Some tests failed")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)