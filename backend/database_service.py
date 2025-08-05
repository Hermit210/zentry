"""
Database service layer providing high-level database operations
This module provides a service layer abstraction over the database operations
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from database import db, DatabaseError, TransactionError
from config import settings
import json

logger = logging.getLogger(__name__)

class DatabaseService:
    """High-level database service providing common operations"""
    
    def __init__(self):
        self.db = db
    
    async def health_check(self) -> Dict[str, Any]:
        """Get comprehensive database health information"""
        try:
            health_status = await self.db.health_check()
            connection_metrics = await self.db.get_connection_metrics()
            
            return {
                "status": health_status.status,
                "type": health_status.type,
                "connection_count": health_status.connection_count,
                "users_count": health_status.users_count,
                "response_time_ms": health_status.response_time_ms,
                "last_check": health_status.last_check.isoformat() if health_status.last_check else None,
                "error": health_status.error,
                "connection_metrics": connection_metrics
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def run_migrations(self) -> Dict[str, Any]:
        """Run database migrations and return status"""
        try:
            success = await self.db.run_migrations()
            return {
                "success": success,
                "message": "Migrations completed successfully" if success else "Migration failed"
            }
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        try:
            return await self.db.optimize_database()
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive user statistics"""
        try:
            if settings.use_in_memory_db:
                # For in-memory database, calculate stats from stored data
                user_data = self.db.in_memory_store["users"].get(user_id)
                if not user_data:
                    return None
                
                user_vms = [vm for vm in self.db.in_memory_store["vms"] if vm.get("user_id") == user_id]
                user_projects = [p for p in self.db.in_memory_store["projects"] if p.get("user_id") == user_id]
                
                return {
                    "user_id": user_id,
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "credits": user_data.get("credits", 0),
                    "total_spent": user_data.get("total_spent", 0),
                    "project_count": len(user_projects),
                    "vm_count": len(user_vms),
                    "running_vm_count": len([vm for vm in user_vms if vm.get("status") == "running"]),
                    "total_uptime_hours": sum(vm.get("uptime_hours", 0) for vm in user_vms),
                    "total_vm_costs": sum(vm.get("total_cost", 0) for vm in user_vms)
                }
            else:
                # Use materialized view for better performance
                result = await self.db.execute_query(
                    "SELECT * FROM user_stats WHERE id = $1",
                    [user_id],
                    fetch_mode="one"
                )
                
                return result.rows[0] if result.rows else None
                
        except Exception as e:
            logger.error(f"Failed to get user statistics for {user_id}: {e}")
            return None
    
    async def log_audit_event(self, user_id: Optional[str], action: str, resource_type: str, 
                            resource_id: Optional[str] = None, old_values: Optional[Dict] = None,
                            new_values: Optional[Dict] = None, ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> bool:
        """Log an audit event"""
        try:
            if settings.use_in_memory_db:
                self.db.in_memory_store["audit_logs"].append({
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "old_values": old_values,
                    "new_values": new_values,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "created_at": datetime.utcnow().isoformat()
                })
            else:
                await self.db.execute_query(
                    """
                    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, 
                                          old_values, new_values, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    [user_id, action, resource_type, resource_id,
                     json.dumps(old_values) if old_values else None,
                     json.dumps(new_values) if new_values else None,
                     ip_address, user_agent],
                    fetch_mode="execute"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    async def get_audit_logs(self, user_id: Optional[str] = None, limit: int = 50, 
                           offset: int = 0) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering"""
        try:
            if settings.use_in_memory_db:
                logs = self.db.in_memory_store["audit_logs"]
                if user_id:
                    logs = [log for log in logs if log.get("user_id") == user_id]
                
                # Sort by created_at descending and apply pagination
                logs = sorted(logs, key=lambda x: x.get("created_at", ""), reverse=True)
                return logs[offset:offset + limit]
            else:
                if user_id:
                    result = await self.db.execute_query(
                        """
                        SELECT * FROM audit_logs 
                        WHERE user_id = $1 
                        ORDER BY created_at DESC 
                        LIMIT $2 OFFSET $3
                        """,
                        [user_id, limit, offset]
                    )
                else:
                    result = await self.db.execute_query(
                        """
                        SELECT * FROM audit_logs 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                        """,
                        [limit, offset]
                    )
                
                return result.rows
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    async def get_system_health_history(self, component: Optional[str] = None, 
                                      hours: int = 24) -> List[Dict[str, Any]]:
        """Get system health history"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            if settings.use_in_memory_db:
                health_records = self.db.in_memory_store["system_health"]
                if component:
                    health_records = [h for h in health_records if h.get("component") == component]
                
                # Filter by time
                filtered_records = []
                for record in health_records:
                    try:
                        record_time = datetime.fromisoformat(record.get("checked_at", ""))
                        if record_time >= since:
                            filtered_records.append(record)
                    except ValueError:
                        continue
                
                return sorted(filtered_records, key=lambda x: x.get("checked_at", ""), reverse=True)
            else:
                if component:
                    result = await self.db.execute_query(
                        """
                        SELECT * FROM system_health 
                        WHERE component = $1 AND checked_at >= $2
                        ORDER BY checked_at DESC
                        """,
                        [component, since]
                    )
                else:
                    result = await self.db.execute_query(
                        """
                        SELECT * FROM system_health 
                        WHERE checked_at >= $1
                        ORDER BY checked_at DESC
                        """,
                        [since]
                    )
                
                return result.rows
                
        except Exception as e:
            logger.error(f"Failed to get system health history: {e}")
            return []
    
    async def cleanup_old_data(self, retention_days: int = 90) -> Dict[str, Any]:
        """Clean up old data based on retention policy"""
        try:
            if settings.use_in_memory_db:
                # For in-memory database, clean up old records
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Clean audit logs
                original_count = len(self.db.in_memory_store["audit_logs"])
                self.db.in_memory_store["audit_logs"] = [
                    log for log in self.db.in_memory_store["audit_logs"]
                    if datetime.fromisoformat(log.get("created_at", "")) >= cutoff_date
                ]
                audit_cleaned = original_count - len(self.db.in_memory_store["audit_logs"])
                
                return {
                    "success": True,
                    "audit_logs_cleaned": audit_cleaned,
                    "retention_days": retention_days
                }
            else:
                result = await self.db.execute_query(
                    "SELECT cleanup_old_audit_logs($1)",
                    [retention_days],
                    fetch_mode="val"
                )
                
                return {
                    "success": True,
                    "records_cleaned": result.rows[0]["value"] if result.rows else 0,
                    "retention_days": retention_days
                }
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            if settings.use_in_memory_db:
                return {
                    "type": "in-memory",
                    "users": len(self.db.in_memory_store["users"]),
                    "projects": len(self.db.in_memory_store["projects"]),
                    "vms": len(self.db.in_memory_store["vms"]),
                    "billing_records": len(self.db.in_memory_store["billing_records"]),
                    "vm_metrics": len(self.db.in_memory_store["vm_metrics"]),
                    "audit_logs": len(self.db.in_memory_store["audit_logs"])
                }
            else:
                # Get table sizes and row counts
                stats_query = """
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
                """
                
                table_stats = await self.db.execute_query(stats_query)
                
                # Get row counts for main tables
                row_counts = {}
                main_tables = ['users', 'projects', 'vms', 'billing_records', 'vm_metrics', 'audit_logs']
                
                for table in main_tables:
                    try:
                        count_result = await self.db.execute_query(
                            f"SELECT COUNT(*) as count FROM {table}",
                            fetch_mode="one"
                        )
                        row_counts[table] = count_result.rows[0]["count"] if count_result.rows else 0
                    except Exception:
                        row_counts[table] = 0
                
                return {
                    "type": "postgresql",
                    "row_counts": row_counts,
                    "table_statistics": table_stats.rows
                }
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {
                "type": "unknown",
                "error": str(e)
            }

# Global database service instance
database_service = DatabaseService()