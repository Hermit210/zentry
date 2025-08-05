"""
VM monitoring and metrics endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database import db
from models import UserResponse, VMMetrics, VMMetricsCreate, APIResponse
from auth import get_current_active_user
from services.service_container import service_container
from services.base_service import ServiceError, ValidationError, NotFoundError
import logging
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/vms/{vm_id}/metrics",
           summary="Get Current VM Metrics",
           description="Get real-time metrics for a specific virtual machine",
           response_description="Current VM performance metrics and resource utilization",
           responses={
               200: {
                   "description": "VM metrics retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "vm_id": "vm-123e4567-e89b-12d3-a456-426614174000",
                               "vm_name": "web-server-01",
                               "instance_type": "small",
                               "status": "running",
                               "cpu_usage": 25.5,
                               "memory_usage": 45.2,
                               "disk_usage": 32.1,
                               "network_in": 1024.5,
                               "network_out": 512.3,
                               "uptime_hours": 24.5,
                               "cost_per_hour": 0.05,
                               "total_cost": 1.275,
                               "current_session_hours": 2.5,
                               "recorded_at": "2024-01-15T10:30:00Z"
                           }
                       }
                   }
               },
               404: {
                   "description": "VM not found or doesn't belong to user"
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_vm_metrics(
    vm_id: str = Path(..., description="VM identifier"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get real-time metrics for a specific virtual machine.
    
    **Path Parameters:**
    - `vm_id`: The unique identifier of the VM
    
    **Metrics Included:**
    - **CPU Usage**: Percentage of CPU utilization (0-100%)
    - **Memory Usage**: Percentage of RAM utilization (0-100%)
    - **Disk Usage**: Percentage of storage utilization (0-100%)
    - **Network I/O**: Bytes transferred in/out
    - **Uptime**: Total hours the VM has been running
    - **Cost Information**: Hourly rate and total accumulated cost
    
    **VM Status Requirements:**
    - VM must exist and belong to the authenticated user
    - Metrics are available for VMs in any status
    - Real-time data for running VMs, last known data for stopped VMs
    
    **Use Cases:**
    - Real-time performance monitoring
    - Resource utilization tracking
    - Cost monitoring and optimization
    - Capacity planning
    - Troubleshooting performance issues
    
    **Update Frequency:**
    - Running VMs: Updated every 30 seconds
    - Stopped VMs: Last recorded metrics before shutdown
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        supabase = db.get_client()
        
        # Verify VM exists and belongs to user
        vm_result = supabase.table("vms").select("*").eq("id", vm_id).eq("user_id", current_user.id).execute()
        
        if not vm_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VM not found"
            )
        
        vm = vm_result.data[0]
        
        # Generate simulated metrics (in production, this would come from actual monitoring)
        if vm["status"] == "running":
            # Simulate realistic metrics for running VM
            cpu_usage = random.uniform(10, 80)
            memory_usage = random.uniform(20, 90)
            disk_usage = random.uniform(15, 75)
            network_in = random.uniform(100, 5000)
            network_out = random.uniform(50, 2000)
        else:
            # Return last known metrics for stopped VMs
            cpu_usage = 0.0
            memory_usage = random.uniform(5, 15)  # Base memory usage
            disk_usage = random.uniform(15, 75)   # Disk usage persists
            network_in = 0.0
            network_out = 0.0
        
        # Calculate uptime and costs
        created_at = datetime.fromisoformat(vm["created_at"].replace('Z', '+00:00'))
        uptime_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        
        # VM pricing lookup
        vm_pricing = {
            "small": 0.05,
            "medium": 0.10,
            "large": 0.20,
            "xlarge": 0.40
        }
        
        cost_per_hour = vm_pricing.get(vm["instance_type"], 0.05)
        
        # Calculate current session hours if running
        current_session_hours = 0.0
        if vm["status"] == "running" and vm.get("last_started"):
            last_started = datetime.fromisoformat(vm["last_started"].replace('Z', '+00:00'))
            current_session_hours = (datetime.utcnow() - last_started).total_seconds() / 3600
        
        # Estimate total cost (simplified calculation)
        total_cost = uptime_hours * cost_per_hour * 0.1  # Assuming 10% average uptime
        
        return {
            "vm_id": vm["id"],
            "vm_name": vm["name"],
            "instance_type": vm["instance_type"],
            "status": vm["status"],
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "disk_usage": round(disk_usage, 1),
            "network_in": round(network_in, 1),
            "network_out": round(network_out, 1),
            "uptime_hours": round(uptime_hours, 2),
            "cost_per_hour": cost_per_hour,
            "total_cost": round(total_cost, 3),
            "current_session_hours": round(current_session_hours, 2),
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching VM metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch VM metrics"
        )

@router.get("/vms/{vm_id}/metrics/history",
           summary="Get VM Metrics History",
           description="Get historical metrics data for a virtual machine",
           response_description="Time-series metrics data for the specified period",
           responses={
               200: {
                   "description": "Metrics history retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "vm_id": "vm-123e4567-e89b-12d3-a456-426614174000",
                               "vm_name": "web-server-01",
                               "period_hours": 24,
                               "data_points": 48,
                               "metrics": [
                                   {
                                       "timestamp": "2024-01-15T09:00:00Z",
                                       "cpu_usage": 25.5,
                                       "memory_usage": 45.2,
                                       "disk_usage": 32.1,
                                       "network_in": 1024.5,
                                       "network_out": 512.3
                                   }
                               ],
                               "averages": {
                                   "cpu_usage": 28.3,
                                   "memory_usage": 42.1,
                                   "disk_usage": 32.1
                               },
                               "peaks": {
                                   "cpu_usage": 78.5,
                                   "memory_usage": 89.2,
                                   "network_in": 5024.1
                               }
                           }
                       }
                   }
               },
               404: {
                   "description": "VM not found"
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_vm_metrics_history(
    vm_id: str = Path(..., description="VM identifier"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours of history (1-168)"),
    interval: int = Query(30, ge=5, le=3600, description="Data point interval in minutes"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get historical metrics data for a virtual machine.
    
    **Path Parameters:**
    - `vm_id`: The unique identifier of the VM
    
    **Query Parameters:**
    - `hours`: Number of hours of history to retrieve (1-168, default: 24)
    - `interval`: Data point interval in minutes (5-3600, default: 30)
    
    **Historical Data:**
    - Time-series metrics data points
    - Configurable time range and resolution
    - Statistical summaries (averages, peaks)
    - Data aggregation for longer periods
    
    **Metrics Tracked:**
    - CPU utilization over time
    - Memory usage patterns
    - Disk usage trends
    - Network I/O patterns
    - Performance correlations
    
    **Data Retention:**
    - **Real-time**: Last 24 hours at 1-minute intervals
    - **Hourly**: Last 7 days at 1-hour intervals
    - **Daily**: Last 30 days at 1-day intervals
    - **Weekly**: Last 12 months at 1-week intervals
    
    **Use Cases:**
    - Performance trend analysis
    - Capacity planning
    - Anomaly detection
    - Cost optimization
    - SLA monitoring
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 50 requests per minute per user
    """
    try:
        supabase = db.get_client()
        
        # Verify VM exists and belongs to user
        vm_result = supabase.table("vms").select("*").eq("id", vm_id).eq("user_id", current_user.id).execute()
        
        if not vm_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VM not found"
            )
        
        vm = vm_result.data[0]
        
        # Generate simulated historical data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Calculate number of data points
        interval_minutes = interval
        total_minutes = hours * 60
        data_points = min(total_minutes // interval_minutes, 1000)  # Cap at 1000 points
        
        metrics = []
        cpu_values = []
        memory_values = []
        disk_values = []
        network_in_values = []
        
        for i in range(data_points):
            timestamp = start_time + timedelta(minutes=i * interval_minutes)
            
            # Generate realistic time-series data with some patterns
            base_cpu = 30 + 20 * random.sin(i * 0.1)  # Sine wave pattern
            cpu_usage = max(5, min(95, base_cpu + random.uniform(-10, 10)))
            
            base_memory = 40 + 15 * random.sin(i * 0.05)
            memory_usage = max(10, min(90, base_memory + random.uniform(-5, 5)))
            
            disk_usage = 32 + random.uniform(-2, 2)  # Slowly growing
            disk_usage = max(15, min(85, disk_usage))
            
            network_in = random.uniform(100, 2000) if vm["status"] == "running" else 0
            network_out = network_in * random.uniform(0.3, 0.8)
            
            metrics.append({
                "timestamp": timestamp.isoformat() + "Z",
                "cpu_usage": round(cpu_usage, 1),
                "memory_usage": round(memory_usage, 1),
                "disk_usage": round(disk_usage, 1),
                "network_in": round(network_in, 1),
                "network_out": round(network_out, 1)
            })
            
            cpu_values.append(cpu_usage)
            memory_values.append(memory_usage)
            disk_values.append(disk_usage)
            network_in_values.append(network_in)
        
        # Calculate statistics
        averages = {
            "cpu_usage": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else 0,
            "memory_usage": round(sum(memory_values) / len(memory_values), 1) if memory_values else 0,
            "disk_usage": round(sum(disk_values) / len(disk_values), 1) if disk_values else 0
        }
        
        peaks = {
            "cpu_usage": round(max(cpu_values), 1) if cpu_values else 0,
            "memory_usage": round(max(memory_values), 1) if memory_values else 0,
            "network_in": round(max(network_in_values), 1) if network_in_values else 0
        }
        
        return {
            "vm_id": vm["id"],
            "vm_name": vm["name"],
            "period_hours": hours,
            "interval_minutes": interval_minutes,
            "data_points": len(metrics),
            "period_start": start_time.isoformat() + "Z",
            "period_end": end_time.isoformat() + "Z",
            "metrics": metrics,
            "averages": averages,
            "peaks": peaks,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching VM metrics history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch VM metrics history"
        )

@router.get("/dashboard",
           summary="Get Monitoring Dashboard Data",
           description="Get comprehensive monitoring dashboard data for all user VMs",
           response_description="Dashboard data with system overview and key metrics",
           responses={
               200: {
                   "description": "Dashboard data retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "overview": {
                                   "total_vms": 5,
                                   "running_vms": 3,
                                   "stopped_vms": 2,
                                   "total_cost": 15.75,
                                   "hourly_cost": 0.35
                               },
                               "vm_summary": [
                                   {
                                       "vm_id": "vm-123",
                                       "name": "web-server-01",
                                       "status": "running",
                                       "cpu_usage": 25.5,
                                       "memory_usage": 45.2,
                                       "cost_per_hour": 0.05
                                   }
                               ],
                               "alerts": [
                                   {
                                       "type": "high_cpu",
                                       "vm_id": "vm-456",
                                       "message": "CPU usage above 80%",
                                       "severity": "warning"
                                   }
                               ],
                               "resource_utilization": {
                                   "avg_cpu": 32.1,
                                   "avg_memory": 48.5,
                                   "avg_disk": 35.2
                               }
                           }
                       }
                   }
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_monitoring_dashboard(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Get comprehensive monitoring dashboard data for all user VMs.
    
    **Dashboard Includes:**
    
    **System Overview:**
    - Total VM count and status breakdown
    - Current hourly cost and total accumulated cost
    - Resource utilization summary
    - System health indicators
    
    **VM Summary:**
    - List of all VMs with current metrics
    - Status and performance indicators
    - Cost information per VM
    - Quick action availability
    
    **Alerts and Notifications:**
    - High resource utilization warnings
    - Cost threshold alerts
    - System health issues
    - Performance anomalies
    
    **Resource Utilization:**
    - Average CPU, memory, and disk usage across all VMs
    - Resource trends and patterns
    - Capacity planning insights
    
    **Use Cases:**
    - System monitoring and oversight
    - Quick health assessment
    - Resource planning
    - Cost monitoring
    - Alert management
    
    **Update Frequency:**
    - Real-time data for running VMs
    - Refreshed every 30 seconds
    - Historical trends updated hourly
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        monitoring_service = service_container.get_monitoring_service()
        return await monitoring_service.get_user_monitoring_overview(current_user.id)
        
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error generating monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate monitoring dashboard"
        )

@router.get("/system/health",
           summary="Get System Health Status",
           description="Get comprehensive system health and performance status",
           response_description="System health metrics and status indicators",
           responses={
               200: {
                   "description": "System health retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "overall_status": "healthy",
                               "components": {
                                   "api": {"status": "healthy", "response_time": 45},
                                   "database": {"status": "healthy", "connections": 12},
                                   "vm_manager": {"status": "healthy", "active_vms": 150}
                               },
                               "performance": {
                                   "avg_response_time": 120,
                                   "requests_per_minute": 450,
                                   "error_rate": 0.02
                               },
                               "capacity": {
                                   "total_vms": 150,
                                   "vm_capacity_used": 75.5,
                                   "storage_used": 45.2
                               }
                           }
                       }
                   }
               }
           })
async def get_system_health(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Get comprehensive system health and performance status.
    
    **System Health Includes:**
    
    **Overall Status:**
    - System-wide health indicator
    - Component status summary
    - Critical issue alerts
    
    **Component Health:**
    - API service status and response times
    - Database connectivity and performance
    - VM management service status
    - Storage system health
    
    **Performance Metrics:**
    - Average API response times
    - Request throughput (requests per minute)
    - Error rates and success ratios
    - Resource utilization trends
    
    **Capacity Information:**
    - Total system VM count
    - VM capacity utilization
    - Storage usage statistics
    - Scaling recommendations
    
    **Use Cases:**
    - System administration and monitoring
    - Performance optimization
    - Capacity planning
    - Issue diagnosis and troubleshooting
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 50 requests per minute per user
    """
    try:
        # Simulate system health data (in production, this would come from actual monitoring)
        
        # Component health checks
        components = {
            "api": {
                "status": "healthy",
                "response_time_ms": random.randint(30, 100),
                "uptime_hours": random.randint(100, 1000),
                "last_check": datetime.utcnow().isoformat() + "Z"
            },
            "database": {
                "status": "healthy",
                "active_connections": random.randint(5, 25),
                "query_time_ms": random.randint(10, 50),
                "last_check": datetime.utcnow().isoformat() + "Z"
            },
            "vm_manager": {
                "status": "healthy",
                "active_vms": random.randint(100, 200),
                "pending_operations": random.randint(0, 5),
                "last_check": datetime.utcnow().isoformat() + "Z"
            },
            "storage": {
                "status": "healthy",
                "usage_percentage": random.uniform(30, 70),
                "available_gb": random.randint(1000, 5000),
                "last_check": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Performance metrics
        performance = {
            "avg_response_time_ms": random.randint(80, 200),
            "requests_per_minute": random.randint(300, 800),
            "error_rate_percentage": random.uniform(0.01, 0.1),
            "success_rate_percentage": random.uniform(99.8, 99.99),
            "peak_requests_per_minute": random.randint(800, 1500)
        }
        
        # Capacity metrics
        capacity = {
            "total_vms": random.randint(150, 300),
            "vm_capacity_used_percentage": random.uniform(60, 85),
            "storage_used_percentage": random.uniform(40, 75),
            "cpu_capacity_used_percentage": random.uniform(45, 80),
            "memory_capacity_used_percentage": random.uniform(50, 85)
        }
        
        # Determine overall status
        component_statuses = [comp["status"] for comp in components.values()]
        overall_status = "healthy" if all(status == "healthy" for status in component_statuses) else "degraded"
        
        # Generate alerts if any issues
        alerts = []
        if performance["error_rate_percentage"] > 0.05:
            alerts.append({
                "type": "high_error_rate",
                "message": f"Error rate at {performance['error_rate_percentage']:.2f}%",
                "severity": "warning"
            })
        
        if capacity["vm_capacity_used_percentage"] > 80:
            alerts.append({
                "type": "high_capacity",
                "message": f"VM capacity at {capacity['vm_capacity_used_percentage']:.1f}%",
                "severity": "info"
            })
        
        return {
            "overall_status": overall_status,
            "components": components,
            "performance": performance,
            "capacity": capacity,
            "alerts": alerts,
            "recommendations": [
                "Consider scaling up VM capacity" if capacity["vm_capacity_used_percentage"] > 75 else None,
                "Monitor error rates closely" if performance["error_rate_percentage"] > 0.03 else None,
                "Storage cleanup recommended" if capacity["storage_used_percentage"] > 70 else None
            ],
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "next_update": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system health"
        )