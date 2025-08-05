from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import VMMetrics, VMMetricsCreate
from .base_service import BaseService, ServiceError, ValidationError, NotFoundError
import random

class MonitoringService(BaseService):
    """VM monitoring and metrics service"""
    
    async def record_vm_metrics(self, vm_id: str, metrics_data: VMMetricsCreate, user_id: str) -> VMMetrics:
        """Record VM metrics"""
        try:
            # Validate VM ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            # Validate metrics data
            await self._validate_metrics_data(metrics_data)
            
            # Create metrics record
            metrics_record = {
                "id": self.generate_id(),
                "vm_id": vm_id,
                "cpu_usage": metrics_data.cpu_usage,
                "memory_usage": metrics_data.memory_usage,
                "disk_usage": metrics_data.disk_usage,
                "network_in": metrics_data.network_in,
                "network_out": metrics_data.network_out,
                "recorded_at": datetime.utcnow()
            }
            
            # Save to database
            created_metrics = await self._create_metrics_record(metrics_record)
            if not created_metrics:
                raise ServiceError("Failed to record VM metrics", "METRICS_RECORD_FAILED")
            
            # Clean up old metrics (keep last 1000 records per VM)
            await self._cleanup_old_metrics(vm_id)
            
            return VMMetrics(**created_metrics)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Metrics recording error: {e}")
            raise ServiceError("Internal server error during metrics recording", "METRICS_ERROR")
    
    async def get_vm_metrics(self, vm_id: str, user_id: str, hours: int = 24, limit: int = 100) -> List[VMMetrics]:
        """Get VM metrics for a time period"""
        try:
            # Validate VM ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get metrics from database
            metrics = await self._get_metrics_by_vm(vm_id, start_time, end_time, limit)
            
            return [VMMetrics(**metric) for metric in metrics]
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting VM metrics: {e}")
            raise ServiceError("Failed to retrieve VM metrics", "METRICS_RETRIEVAL_ERROR")
    
    async def get_latest_vm_metrics(self, vm_id: str, user_id: str) -> Optional[VMMetrics]:
        """Get latest metrics for a VM"""
        try:
            # Validate VM ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            # Get latest metrics
            latest_metrics = await self._get_latest_metrics_by_vm(vm_id)
            
            if latest_metrics:
                return VMMetrics(**latest_metrics)
            
            return None
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting latest VM metrics: {e}")
            raise ServiceError("Failed to retrieve latest VM metrics", "LATEST_METRICS_ERROR")
    
    async def generate_mock_metrics(self, vm_id: str, user_id: str) -> VMMetrics:
        """Generate mock metrics for demonstration purposes"""
        try:
            # Validate VM ownership
            if not await self.validate_user_ownership(user_id, "vms", vm_id):
                raise NotFoundError("VM", vm_id)
            
            # Generate realistic mock metrics
            mock_metrics = VMMetricsCreate(
                cpu_usage=random.uniform(10, 80),
                memory_usage=random.uniform(20, 90),
                disk_usage=random.uniform(15, 70),
                network_in=random.uniform(0, 100),
                network_out=random.uniform(0, 100)
            )
            
            return await self.record_vm_metrics(vm_id, mock_metrics, user_id)
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error generating mock metrics: {e}")
            raise ServiceError("Failed to generate mock metrics", "MOCK_METRICS_ERROR")
    
    async def get_vm_metrics_summary(self, vm_id: str, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get VM metrics summary with averages and trends"""
        try:
            # Get metrics for the period
            metrics = await self.get_vm_metrics(vm_id, user_id, hours)
            
            if not metrics:
                return {
                    "vm_id": vm_id,
                    "period_hours": hours,
                    "data_points": 0,
                    "averages": {},
                    "peaks": {},
                    "trends": {}
                }
            
            # Calculate averages
            avg_cpu = sum(m.cpu_usage for m in metrics) / len(metrics)
            avg_memory = sum(m.memory_usage for m in metrics) / len(metrics)
            avg_disk = sum(m.disk_usage for m in metrics) / len(metrics)
            avg_network_in = sum(m.network_in for m in metrics) / len(metrics)
            avg_network_out = sum(m.network_out for m in metrics) / len(metrics)
            
            # Calculate peaks
            peak_cpu = max(m.cpu_usage for m in metrics)
            peak_memory = max(m.memory_usage for m in metrics)
            peak_disk = max(m.disk_usage for m in metrics)
            peak_network_in = max(m.network_in for m in metrics)
            peak_network_out = max(m.network_out for m in metrics)
            
            # Calculate trends (simple linear trend)
            trends = await self._calculate_trends(metrics)
            
            return {
                "vm_id": vm_id,
                "period_hours": hours,
                "data_points": len(metrics),
                "averages": {
                    "cpu_usage": round(avg_cpu, 2),
                    "memory_usage": round(avg_memory, 2),
                    "disk_usage": round(avg_disk, 2),
                    "network_in": round(avg_network_in, 2),
                    "network_out": round(avg_network_out, 2)
                },
                "peaks": {
                    "cpu_usage": round(peak_cpu, 2),
                    "memory_usage": round(peak_memory, 2),
                    "disk_usage": round(peak_disk, 2),
                    "network_in": round(peak_network_in, 2),
                    "network_out": round(peak_network_out, 2)
                },
                "trends": trends,
                "latest_metrics": metrics[0] if metrics else None
            }
            
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            raise ServiceError("Failed to retrieve metrics summary", "METRICS_SUMMARY_ERROR")
    
    async def get_user_monitoring_overview(self, user_id: str) -> Dict[str, Any]:
        """Get monitoring overview for all user's VMs"""
        try:
            # Get user's VMs
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vms").select("*").eq("user_id", user_id).eq("status", "running").execute()
                vms = result.data or []
            else:
                memory_store = self.db.get_memory_store()
                vms = [
                    vm for vm in memory_store["vms"] 
                    if vm.get("user_id") == user_id and vm.get("status") == "running"
                ]
            
            vm_summaries = []
            total_avg_cpu = 0
            total_avg_memory = 0
            total_vms = len(vms)
            
            for vm in vms:
                # Get latest metrics for each VM
                latest_metrics = await self._get_latest_metrics_by_vm(vm["id"])
                
                if latest_metrics:
                    vm_summary = {
                        "vm_id": vm["id"],
                        "vm_name": vm["name"],
                        "instance_type": vm["instance_type"],
                        "latest_metrics": VMMetrics(**latest_metrics),
                        "status": "monitored"
                    }
                    total_avg_cpu += latest_metrics["cpu_usage"]
                    total_avg_memory += latest_metrics["memory_usage"]
                else:
                    vm_summary = {
                        "vm_id": vm["id"],
                        "vm_name": vm["name"],
                        "instance_type": vm["instance_type"],
                        "latest_metrics": None,
                        "status": "no_data"
                    }
                
                vm_summaries.append(vm_summary)
            
            # Calculate overall averages
            overall_avg_cpu = (total_avg_cpu / total_vms) if total_vms > 0 else 0
            overall_avg_memory = (total_avg_memory / total_vms) if total_vms > 0 else 0
            
            return {
                "user_id": user_id,
                "total_running_vms": total_vms,
                "monitored_vms": len([vm for vm in vm_summaries if vm["status"] == "monitored"]),
                "overall_averages": {
                    "cpu_usage": round(overall_avg_cpu, 2),
                    "memory_usage": round(overall_avg_memory, 2)
                },
                "vm_summaries": vm_summaries,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monitoring overview: {e}")
            raise ServiceError("Failed to retrieve monitoring overview", "MONITORING_OVERVIEW_ERROR")
    
    async def health_check(self) -> Dict[str, Any]:
        """Monitoring service health check"""
        try:
            # Test metrics lookup functionality
            test_result = await self._get_metrics_by_vm("test-vm-id", datetime.utcnow() - timedelta(hours=1), datetime.utcnow(), 1)
            
            return {
                "service": "monitoring",
                "status": "healthy",
                "database_connection": "ok",
                "metrics_operations": "ok"
            }
        except Exception as e:
            return {
                "service": "monitoring",
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_metrics_data(self, metrics_data: VMMetricsCreate):
        """Validate metrics data"""
        if not (0 <= metrics_data.cpu_usage <= 100):
            raise ValidationError("CPU usage must be between 0 and 100")
        
        if not (0 <= metrics_data.memory_usage <= 100):
            raise ValidationError("Memory usage must be between 0 and 100")
        
        if not (0 <= metrics_data.disk_usage <= 100):
            raise ValidationError("Disk usage must be between 0 and 100")
        
        if metrics_data.network_in < 0:
            raise ValidationError("Network input must be non-negative")
        
        if metrics_data.network_out < 0:
            raise ValidationError("Network output must be non-negative")
    
    async def _create_metrics_record(self, metrics_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create metrics record in database"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vm_metrics").insert(metrics_record).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                memory_store["vm_metrics"].append(metrics_record)
                return metrics_record
        except Exception as e:
            self.logger.error(f"Error creating metrics record: {e}")
            return None
    
    async def _get_metrics_by_vm(self, vm_id: str, start_time: datetime, end_time: datetime, limit: int) -> List[Dict[str, Any]]:
        """Get metrics by VM and time range"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vm_metrics").select("*").eq("vm_id", vm_id).gte("recorded_at", start_time.isoformat()).lte("recorded_at", end_time.isoformat()).order("recorded_at", desc=True).limit(limit).execute()
                return result.data or []
            else:
                memory_store = self.db.get_memory_store()
                metrics = [
                    metric for metric in memory_store["vm_metrics"]
                    if (metric.get("vm_id") == vm_id and
                        start_time <= datetime.fromisoformat(metric.get("recorded_at", "1970-01-01")) <= end_time)
                ]
                # Sort by recorded_at descending and limit
                metrics = sorted(metrics, key=lambda x: x.get("recorded_at", datetime.min), reverse=True)
                return metrics[:limit]
        except Exception as e:
            self.logger.error(f"Error getting metrics by VM: {e}")
            return []
    
    async def _get_latest_metrics_by_vm(self, vm_id: str) -> Optional[Dict[str, Any]]:
        """Get latest metrics for a VM"""
        try:
            if self.db.get_client():
                supabase = self.db.get_client()
                result = supabase.table("vm_metrics").select("*").eq("vm_id", vm_id).order("recorded_at", desc=True).limit(1).execute()
                return result.data[0] if result.data else None
            else:
                memory_store = self.db.get_memory_store()
                vm_metrics = [
                    metric for metric in memory_store["vm_metrics"]
                    if metric.get("vm_id") == vm_id
                ]
                if vm_metrics:
                    return max(vm_metrics, key=lambda x: x.get("recorded_at", datetime.min))
                return None
        except Exception as e:
            self.logger.error(f"Error getting latest metrics: {e}")
            return None
    
    async def _cleanup_old_metrics(self, vm_id: str, keep_count: int = 1000):
        """Clean up old metrics, keeping only the most recent records"""
        try:
            if self.db.get_client():
                # For Supabase, we'd need a more complex query or stored procedure
                # For now, we'll skip cleanup in production
                pass
            else:
                memory_store = self.db.get_memory_store()
                vm_metrics = [
                    metric for metric in memory_store["vm_metrics"]
                    if metric.get("vm_id") == vm_id
                ]
                
                if len(vm_metrics) > keep_count:
                    # Sort by recorded_at and keep only the most recent
                    vm_metrics.sort(key=lambda x: x.get("recorded_at", datetime.min), reverse=True)
                    metrics_to_keep = vm_metrics[:keep_count]
                    
                    # Remove old metrics from memory store
                    memory_store["vm_metrics"] = [
                        metric for metric in memory_store["vm_metrics"]
                        if metric.get("vm_id") != vm_id or metric in metrics_to_keep
                    ]
        except Exception as e:
            self.logger.warning(f"Error cleaning up old metrics: {e}")
    
    async def _calculate_trends(self, metrics: List[VMMetrics]) -> Dict[str, str]:
        """Calculate simple trends for metrics"""
        try:
            if len(metrics) < 2:
                return {
                    "cpu_usage": "stable",
                    "memory_usage": "stable",
                    "disk_usage": "stable"
                }
            
            # Simple trend calculation: compare first half with second half
            mid_point = len(metrics) // 2
            first_half = metrics[mid_point:]  # Older data (metrics are sorted desc)
            second_half = metrics[:mid_point]  # Newer data
            
            def calculate_trend(first_values, second_values):
                first_avg = sum(first_values) / len(first_values)
                second_avg = sum(second_values) / len(second_values)
                
                if second_avg > first_avg * 1.1:
                    return "increasing"
                elif second_avg < first_avg * 0.9:
                    return "decreasing"
                else:
                    return "stable"
            
            return {
                "cpu_usage": calculate_trend(
                    [m.cpu_usage for m in first_half],
                    [m.cpu_usage for m in second_half]
                ),
                "memory_usage": calculate_trend(
                    [m.memory_usage for m in first_half],
                    [m.memory_usage for m in second_half]
                ),
                "disk_usage": calculate_trend(
                    [m.disk_usage for m in first_half],
                    [m.disk_usage for m in second_half]
                )
            }
        except Exception as e:
            self.logger.error(f"Error calculating trends: {e}")
            return {
                "cpu_usage": "unknown",
                "memory_usage": "unknown",
                "disk_usage": "unknown"
            }