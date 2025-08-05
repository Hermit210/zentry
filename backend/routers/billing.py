"""
Billing and credit management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from database import db
from models import (
    UserResponse, BillingRecord, BillingRecordCreate, UsageSummary, 
    CreditUpdate, APIResponse, PaginationParams, PaginatedResponse
)
from auth import get_current_active_user
from services.service_container import service_container
from services.base_service import ServiceError, ValidationError, NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/credits",
           summary="Get Current Credit Balance",
           description="Get current user's credit balance and spending summary",
           response_description="Current credit balance with spending statistics",
           responses={
               200: {
                   "description": "Credit information retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "current_credits": 45.25,
                               "total_spent": 4.75,
                               "monthly_spending": 2.30,
                               "weekly_spending": 0.85,
                               "daily_spending": 0.15,
                               "projected_monthly_cost": 6.90,
                               "last_transaction": "2024-01-15T10:30:00Z",
                               "credit_history_count": 12
                           }
                       }
                   }
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_credit_balance(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Get current user's credit balance and spending summary.
    
    **Returns:**
    - Current available credit balance
    - Total amount spent to date
    - Spending breakdown (monthly, weekly, daily)
    - Projected monthly cost based on current usage
    - Last transaction timestamp
    - Credit history count
    
    **Use Cases:**
    - Check available credits before creating VMs
    - Monitor spending patterns and trends
    - Budget planning and cost control
    - Account balance verification
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        supabase = db.get_client()
        
        # Get recent billing records for calculations
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        # Calculate spending periods
        monthly_records = supabase.table("billing_records").select("amount").eq("user_id", current_user.id).gte("created_at", thirty_days_ago.isoformat()).execute()
        weekly_records = supabase.table("billing_records").select("amount").eq("user_id", current_user.id).gte("created_at", seven_days_ago.isoformat()).execute()
        daily_records = supabase.table("billing_records").select("amount").eq("user_id", current_user.id).gte("created_at", one_day_ago.isoformat()).execute()
        
        monthly_spending = sum(record["amount"] for record in monthly_records.data if record["amount"] > 0)
        weekly_spending = sum(record["amount"] for record in weekly_records.data if record["amount"] > 0)
        daily_spending = sum(record["amount"] for record in daily_records.data if record["amount"] > 0)
        
        # Get last transaction
        last_transaction_result = supabase.table("billing_records").select("created_at").eq("user_id", current_user.id).order("created_at", desc=True).limit(1).execute()
        last_transaction = last_transaction_result.data[0]["created_at"] if last_transaction_result.data else None
        
        # Get total credit history count
        history_count_result = supabase.table("billing_records").select("id", count="exact").eq("user_id", current_user.id).execute()
        history_count = history_count_result.count or 0
        
        # Calculate projected monthly cost based on daily average
        projected_monthly = daily_spending * 30 if daily_spending > 0 else 0
        
        return {
            "current_credits": current_user.credits,
            "total_spent": current_user.total_spent,
            "monthly_spending": monthly_spending,
            "weekly_spending": weekly_spending,
            "daily_spending": daily_spending,
            "projected_monthly_cost": projected_monthly,
            "last_transaction": last_transaction,
            "credit_history_count": history_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error fetching credit balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch credit balance"
        )

@router.get("/history",
           response_model=PaginatedResponse,
           summary="Get Billing History",
           description="Get paginated billing history with transaction details",
           response_description="Paginated list of billing transactions",
           responses={
               200: {
                   "description": "Billing history retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "items": [
                                   {
                                       "id": "bill-123e4567-e89b-12d3-a456-426614174000",
                                       "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                       "vm_id": "vm-123e4567-e89b-12d3-a456-426614174000",
                                       "action_type": "vm_running",
                                       "amount": 0.05,
                                       "description": "VM usage: web-server-01 (1 hour)",
                                       "created_at": "2024-01-15T10:30:00Z"
                                   }
                               ],
                               "total": 25,
                               "page": 1,
                               "limit": 20,
                               "pages": 2,
                               "has_next": True,
                               "has_prev": False
                           }
                       }
                   }
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_billing_history(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    vm_id: Optional[str] = Query(None, description="Filter by VM ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get paginated billing history with optional filtering.
    
    **Query Parameters:**
    - `page`: Page number (1-based, default: 1)
    - `limit`: Records per page (1-100, default: 20)
    - `action_type`: Filter by transaction type (vm_create, vm_running, credit_add, etc.)
    - `vm_id`: Filter by specific VM ID
    - `start_date`: Filter from date (ISO format: 2024-01-15T00:00:00Z)
    - `end_date`: Filter to date (ISO format: 2024-01-15T23:59:59Z)
    
    **Transaction Types:**
    - `vm_create`: VM creation charges
    - `vm_running`: Hourly usage charges
    - `vm_start`: VM start operation charges
    - `credit_add`: Credit additions
    - `credit_deduct`: Manual credit deductions
    
    **Response:**
    - Paginated list of billing records
    - Total count and pagination metadata
    - Detailed transaction information
    
    **Use Cases:**
    - Review spending history and patterns
    - Track VM usage costs
    - Generate expense reports
    - Audit billing transactions
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        supabase = db.get_client()
        
        # Build query
        query = supabase.table("billing_records").select("*").eq("user_id", current_user.id)
        
        # Apply filters
        if action_type:
            query = query.eq("action_type", action_type)
        if vm_id:
            query = query.eq("vm_id", vm_id)
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data)
        
        # Apply pagination
        offset = (page - 1) * limit
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Convert to response models
        items = []
        for record in result.data:
            items.append(BillingRecord(
                id=record["id"],
                user_id=record["user_id"],
                vm_id=record.get("vm_id"),
                action_type=record["action_type"],
                amount=record["amount"],
                description=record["description"],
                created_at=record["created_at"]
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error fetching billing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing history"
        )

@router.get("/usage-summary",
           response_model=UsageSummary,
           summary="Get Usage Summary",
           description="Get comprehensive usage and cost summary for specified period",
           response_description="Detailed usage statistics and cost breakdown",
           responses={
               200: {
                   "description": "Usage summary retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "user_id": "123e4567-e89b-12d3-a456-426614174000",
                               "current_credits": 45.25,
                               "total_spent": 4.75,
                               "active_vms": 2,
                               "total_vms": 5,
                               "billing_records_count": 25,
                               "period_start": "2024-01-01T00:00:00Z",
                               "period_end": "2024-01-31T23:59:59Z",
                               "hourly_cost": 0.15,
                               "projected_monthly_cost": 108.00
                           }
                       }
                   }
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_usage_summary(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get comprehensive usage and cost summary.
    
    **Query Parameters:**
    - `period_days`: Number of days to include (1-365, default: 30)
    
    **Summary Includes:**
    - Current credit balance and total spent
    - Active and total VM counts
    - Billing transaction count for period
    - Current hourly cost of running VMs
    - Projected monthly cost based on current usage
    - Period start and end dates
    
    **Calculations:**
    - **Hourly Cost**: Sum of cost_per_hour for all running VMs
    - **Projected Monthly**: Hourly cost × 24 hours × 30 days
    - **Period Spending**: Total charges within specified period
    - **Active VMs**: VMs currently in 'running' status
    
    **Use Cases:**
    - Monthly/quarterly cost reporting
    - Budget planning and forecasting
    - Usage trend analysis
    - Cost optimization planning
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        billing_service = service_container.get_billing_service()
        return await billing_service.get_usage_summary(current_user.id, period_days)
        
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error generating usage summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage summary"
        )

@router.post("/credits/add",
            response_model=APIResponse,
            summary="Add Credits to Account",
            description="Add credits to user account (admin only or payment integration)",
            response_description="Credit addition confirmation with updated balance",
            responses={
                200: {
                    "description": "Credits added successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "message": "Credits added successfully",
                                "data": {
                                    "amount_added": 25.00,
                                    "new_balance": 70.25,
                                    "transaction_id": "bill-123e4567-e89b-12d3-a456-426614174000"
                                }
                            }
                        }
                    }
                },
                400: {
                    "description": "Invalid credit amount or validation error"
                },
                401: {
                    "description": "Authentication required"
                },
                403: {
                    "description": "Insufficient permissions (admin required)"
                }
            })
async def add_credits(
    credit_data: CreditUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Add credits to user account.
    
    **Request Body:**
    ```json
    {
        "amount": 25.00,
        "description": "Credit card payment - $25.00"
    }
    ```
    
    **Features:**
    - Adds specified amount to user's credit balance
    - Creates billing record for transaction tracking
    - Updates user's total credit history
    - Validates credit amount (must be positive)
    
    **Validation:**
    - Amount must be positive (> 0)
    - Maximum single addition: $1000
    - Description optional but recommended
    
    **Use Cases:**
    - Payment processing integration
    - Manual credit adjustments (admin)
    - Promotional credit additions
    - Account top-ups
    
    **Security:**
    - Currently requires authentication
    - In production: admin-only or payment gateway integration
    - All transactions logged for audit
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 10 requests per minute per user
    """
    try:
        billing_service = service_container.get_billing_service()
        billing_record = await billing_service.add_credits(
            current_user.id, 
            credit_data.amount, 
            credit_data.description or f"Credit addition: ${credit_data.amount:.2f}"
        )
        
        # Get updated user credits
        user_service = service_container.get_user_service()
        updated_user = await user_service.get_user_by_id(current_user.id)
        
        return APIResponse(
            success=True,
            message="Credits added successfully",
            data={
                "amount_added": credit_data.amount,
                "previous_balance": current_user.credits,
                "new_balance": updated_user.credits,
                "transaction_id": billing_record.id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credits"
        )

@router.get("/cost-analysis",
           summary="Get Cost Analysis",
           description="Get detailed cost analysis and spending patterns",
           response_description="Comprehensive cost breakdown and analysis",
           responses={
               200: {
                   "description": "Cost analysis retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "total_cost": 4.75,
                               "cost_by_vm_type": {
                                   "small": 2.50,
                                   "medium": 2.25
                               },
                               "cost_by_action": {
                                   "vm_running": 4.50,
                                   "vm_create": 0.25
                               },
                               "daily_average": 0.15,
                               "weekly_trend": [0.10, 0.12, 0.15, 0.18, 0.20, 0.15, 0.12],
                               "most_expensive_vm": {
                                   "vm_id": "vm-123",
                                   "name": "web-server-01",
                                   "cost": 2.50
                               },
                               "cost_optimization_tips": [
                                   "Stop unused VMs to reduce costs",
                                   "Consider smaller instance types for development"
                               ]
                           }
                       }
                   }
               },
               401: {
                   "description": "Authentication required"
               }
           })
async def get_cost_analysis(
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get detailed cost analysis and spending patterns.
    
    **Query Parameters:**
    - `period_days`: Analysis period in days (1-365, default: 30)
    
    **Analysis Includes:**
    - Total cost for the period
    - Cost breakdown by VM instance type
    - Cost breakdown by action type
    - Daily average spending
    - Weekly spending trend
    - Most expensive VM identification
    - Cost optimization recommendations
    
    **Cost Optimization Tips:**
    - Identifies unused or underutilized VMs
    - Suggests instance type optimizations
    - Highlights spending patterns
    - Provides actionable recommendations
    
    **Use Cases:**
    - Cost optimization planning
    - Spending pattern analysis
    - Budget variance analysis
    - Resource utilization review
    
    **Authentication:** Requires valid JWT token
    
    **Rate Limit:** 50 requests per minute per user
    """
    try:
        supabase = db.get_client()
        
        # Calculate period
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # Get billing records for period
        billing_result = supabase.table("billing_records").select("*").eq("user_id", current_user.id).gte("created_at", period_start.isoformat()).execute()
        
        records = billing_result.data
        total_cost = sum(record["amount"] for record in records if record["amount"] > 0)
        
        # Cost by action type
        cost_by_action = {}
        for record in records:
            if record["amount"] > 0:
                action = record["action_type"]
                cost_by_action[action] = cost_by_action.get(action, 0) + record["amount"]
        
        # Get VM information for cost by type analysis
        vms_result = supabase.table("vms").select("id, name, instance_type").eq("user_id", current_user.id).execute()
        vm_info = {vm["id"]: vm for vm in vms_result.data}
        
        # Cost by VM type
        cost_by_vm_type = {}
        vm_costs = {}
        
        for record in records:
            if record["amount"] > 0 and record.get("vm_id"):
                vm_id = record["vm_id"]
                if vm_id in vm_info:
                    vm_type = vm_info[vm_id]["instance_type"]
                    cost_by_vm_type[vm_type] = cost_by_vm_type.get(vm_type, 0) + record["amount"]
                    vm_costs[vm_id] = vm_costs.get(vm_id, 0) + record["amount"]
        
        # Find most expensive VM
        most_expensive_vm = None
        if vm_costs:
            most_expensive_vm_id = max(vm_costs, key=vm_costs.get)
            if most_expensive_vm_id in vm_info:
                most_expensive_vm = {
                    "vm_id": most_expensive_vm_id,
                    "name": vm_info[most_expensive_vm_id]["name"],
                    "cost": vm_costs[most_expensive_vm_id]
                }
        
        # Calculate daily average
        daily_average = total_cost / period_days if period_days > 0 else 0
        
        # Generate weekly trend (simplified)
        weekly_trend = []
        for i in range(7):
            week_start = datetime.utcnow() - timedelta(days=(i+1)*7)
            week_end = datetime.utcnow() - timedelta(days=i*7)
            
            week_records = [r for r in records 
                          if week_start.isoformat() <= r["created_at"] <= week_end.isoformat()]
            week_cost = sum(r["amount"] for r in week_records if r["amount"] > 0)
            weekly_trend.append(round(week_cost, 2))
        
        weekly_trend.reverse()  # Oldest to newest
        
        # Generate cost optimization tips
        optimization_tips = []
        
        # Check for stopped VMs that might be forgotten
        stopped_vms = [vm for vm in vms_result.data if vm.get("status") == "stopped"]
        if stopped_vms:
            optimization_tips.append(f"You have {len(stopped_vms)} stopped VMs. Consider terminating unused ones.")
        
        # Check for high-cost VMs
        if most_expensive_vm and most_expensive_vm["cost"] > total_cost * 0.5:
            optimization_tips.append(f"VM '{most_expensive_vm['name']}' accounts for over 50% of your costs. Consider optimization.")
        
        # Check spending trend
        if len(weekly_trend) >= 2 and weekly_trend[-1] > weekly_trend[-2] * 1.5:
            optimization_tips.append("Your spending has increased significantly this week. Review recent VM usage.")
        
        if not optimization_tips:
            optimization_tips.append("Your spending patterns look optimized. Keep monitoring for changes.")
        
        return {
            "period_days": period_days,
            "period_start": period_start.isoformat() + "Z",
            "period_end": datetime.utcnow().isoformat() + "Z",
            "total_cost": round(total_cost, 2),
            "cost_by_vm_type": {k: round(v, 2) for k, v in cost_by_vm_type.items()},
            "cost_by_action": {k: round(v, 2) for k, v in cost_by_action.items()},
            "daily_average": round(daily_average, 2),
            "weekly_trend": weekly_trend,
            "most_expensive_vm": most_expensive_vm,
            "cost_optimization_tips": optimization_tips,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error generating cost analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cost analysis"
        )