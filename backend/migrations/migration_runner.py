"""
Database migration runner for Zentry Cloud
Handles running SQL migration files and tracking migration state
"""

import os
import logging
import time
from pathlib import Path
from typing import List, Optional
import asyncpg
from config import settings

logger = logging.getLogger(__name__)

class MigrationRunner:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.migrations_dir = Path(__file__).parent
        
    async def create_migrations_table(self, conn):
        """Create the migrations tracking table if it doesn't exist"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def get_applied_migrations(self, conn) -> List[str]:
        """Get list of already applied migrations"""
        try:
            rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
            return [row['version'] for row in rows]
        except Exception as e:
            logger.warning(f"Could not fetch applied migrations: {e}")
            return []
    
    async def get_pending_migrations(self) -> List[tuple]:
        """Get list of pending migration files"""
        migration_files = []
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            if file_path.name.startswith("00"):  # Only numbered migrations
                version = file_path.stem
                migration_files.append((version, file_path))
        
        if not self.database_url:
            logger.info("No database URL configured, skipping migration check")
            return migration_files
        
        try:
            conn = await asyncpg.connect(self.database_url)
            await self.create_migrations_table(conn)
            applied = await self.get_applied_migrations(conn)
            await conn.close()
            
            # Filter out already applied migrations
            pending = [(v, p) for v, p in migration_files if v not in applied]
            return pending
            
        except Exception as e:
            logger.error(f"Could not check migration status: {e}")
            return migration_files
    
    async def run_migration(self, version: str, file_path: Path) -> bool:
        """Run a single migration file with enhanced error handling"""
        if not self.database_url:
            logger.info(f"No database URL configured, skipping migration {version}")
            return True
        
        conn = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Validate SQL content
            if not sql_content.strip():
                logger.warning(f"Migration {version} is empty, skipping")
                return True
            
            conn = await asyncpg.connect(
                self.database_url,
                command_timeout=300  # 5 minutes for migrations
            )
            
            logger.info(f"Starting migration {version}")
            start_time = time.time()
            
            # Run the migration in a transaction
            async with conn.transaction():
                # Split SQL content by statements if needed
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for i, statement in enumerate(statements):
                    try:
                        await conn.execute(statement)
                        logger.debug(f"Migration {version}: executed statement {i+1}/{len(statements)}")
                    except Exception as stmt_error:
                        logger.error(f"Migration {version} failed at statement {i+1}: {stmt_error}")
                        logger.error(f"Failed statement: {statement[:200]}...")
                        raise
                
                # Record successful migration
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)",
                    version
                )
            
            execution_time = time.time() - start_time
            logger.info(f"Successfully applied migration {version} in {execution_time:.2f}s")
            return True
            
        except asyncpg.PostgresError as e:
            logger.error(f"PostgreSQL error in migration {version}: {e}")
            logger.error(f"Error code: {e.sqlstate}, Detail: {e.detail}")
            return False
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
        finally:
            if conn:
                await conn.close()
    
    async def run_pending_migrations(self) -> bool:
        """Run all pending migrations with comprehensive error handling"""
        try:
            # First check database connectivity
            if not await self.check_database_connection():
                logger.error("Database connection check failed, cannot run migrations")
                return False
            
            pending = await self.get_pending_migrations()
            
            if not pending:
                logger.info("No pending migrations")
                return True
            
            logger.info(f"Found {len(pending)} pending migrations: {[v for v, _ in pending]}")
            
            # Run migrations in order
            for version, file_path in pending:
                logger.info(f"Running migration {version}...")
                success = await self.run_migration(version, file_path)
                if not success:
                    logger.error(f"Migration {version} failed, stopping migration process")
                    return False
                logger.info(f"Migration {version} completed successfully")
            
            logger.info("All migrations completed successfully")
            
            # Verify final state
            await self._verify_schema_integrity()
            
            return True
            
        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False
    
    async def _verify_schema_integrity(self):
        """Verify database schema integrity after migrations"""
        if not self.database_url:
            return
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Check that all expected tables exist
            expected_tables = ['users', 'projects', 'vms', 'billing_records', 'vm_metrics', 
                             'audit_logs', 'system_health', 'vm_state_transitions']
            
            existing_tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            
            existing_table_names = {row['table_name'] for row in existing_tables}
            missing_tables = set(expected_tables) - existing_table_names
            
            if missing_tables:
                logger.warning(f"Missing expected tables: {missing_tables}")
            else:
                logger.info("All expected tables are present")
            
            # Check for any constraint violations
            constraint_check = await conn.fetch("""
                SELECT conname, conrelid::regclass 
                FROM pg_constraint 
                WHERE NOT convalidated
            """)
            
            if constraint_check:
                logger.warning(f"Found unvalidated constraints: {constraint_check}")
            
            await conn.close()
            
        except Exception as e:
            logger.warning(f"Schema integrity check failed: {e}")
    
    async def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration (if rollback script exists)"""
        if not self.database_url:
            logger.info(f"No database URL configured, skipping rollback of {version}")
            return True
        
        rollback_file = self.migrations_dir / f"{version}_rollback.sql"
        
        if not rollback_file.exists():
            logger.error(f"No rollback script found for migration {version}")
            return False
        
        try:
            with open(rollback_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            conn = await asyncpg.connect(self.database_url)
            
            async with conn.transaction():
                await conn.execute(sql_content)
                await conn.execute(
                    "DELETE FROM schema_migrations WHERE version = $1",
                    version
                )
            
            await conn.close()
            logger.info(f"Successfully rolled back migration {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
    
    async def check_database_connection(self) -> bool:
        """Check if database connection is working"""
        if not self.database_url:
            logger.info("No database URL configured, using in-memory storage")
            return True
        
        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute("SELECT 1")
            await conn.close()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

# Global migration runner instance
migration_runner = MigrationRunner()

async def run_migrations():
    """Convenience function to run all pending migrations"""
    return await migration_runner.run_pending_migrations()

async def check_database():
    """Convenience function to check database connection"""
    return await migration_runner.check_database_connection()