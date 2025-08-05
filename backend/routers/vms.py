from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from database import db
from models import VMCreate, VMResponse, UserResponse, APIResponse, VMStatus
from auth import get_current_active_user
from services.service_container import service_container
from services.base_service import ServiceError, ValidationError, NotFoundError, InsufficientCreditsError
import logging
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])



@router.post("/", 
             response_model=VMResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="Create Virtual Machine",
             description="Create a new virtual machine in a specified project with automatic credit deduction",
             response_description="Complete VM information including IP address, specifications, and cost details",
             responses={
                 201: {
                     "description": "VM created successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": "vm-123e4567-e89b-12d3-a456-426614174000",
                                 "name": "web-server-01",
                                 "instance_type": "small",
                                 "image": "ubuntu-22.04",
                                 "status": "running",
                                 "ip_address": "192.168.1.10",
                                 "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                 "project_id": "proj-123e4567-e89b-12d3-a456-426614174000",
                                 "specs": {
                                     "cpu": "1 vCPU",
                                     "ram": "1 GB", 
                                     "storage": "20 GB SSD"
                                 },
                                 "cost_per_hour": 0.05,
                                 "uptime_hours": 0.0,
                                 "total_cost": 0.05,
                                 "current_session_hours": 0.0,
                                 "created_at": "2024-01-15T10:30:00Z",
                                 "last_started": "2024-01-15T10:30:00Z"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "VM creation failed - insufficient credits or validation error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Insufficient credits. Need at least $0.05 for small instance"
                             }
                         }
                     }
                 },
                 404: {
                     "description": "Project not found or doesn't belong to user",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Project not found"
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Authentication required"
                 }
             })
async def create_vm(
    vm_data: VMCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Create a new virtual machine in a project.
    
    **Features:**
    - Creates VM with specified configuration and OS image
    - Assigns unique IP address automatically
    - Deducts creation cost from user credits
    - Starts VM automatically after creation
    - Associates VM with specified project
    
    **Instance Types & Pricing:**
    - **small**: 1 vCPU, 1GB RAM, 20GB SSD - $0.05/hour
    - **medium**: 2 vCPU, 4GB RAM, 40GB SSD - $0.10/hour  
    - **large**: 4 vCPU, 8GB RAM, 80GB SSD - $0.20/hour
    - **xlarge**: 8 vCPU, 16GB RAM, 160GB SSD - $0.40/hour
    
    **Available OS Images:**
    - ubuntu-22.04 (Ubuntu 22.04 LTS)
    - ubuntu-20.04 (Ubuntu 20.04 LTS)
    - centos-8 (CentOS 8)
    - debian-11 (Debian 11)
    - fedora-38 (Fedora 38)
    
    **Requirements:**
    - Valid project ID that belongs to the user
    - Sufficient credits for the instance type
    - Unique VM name within the project
    - Valid authentication token
    
    **Request Body:**
    ```json
    {
        "name": "web-server-01",
        "instance_type": "small",
        "image": "ubuntu-22.04", 
        "project_id": "proj-123e4567-e89b-12d3-a456-426614174000"
    }
    ```
    
    **Cost Structure:**
    - One-time creation fee (varies by instance type)
    - Hourly usage charges while VM is running
    - No charges when VM is stopped
    - Automatic credit deduction
    
    **Rate Limit:** 10 requests per minute per user
    """
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.create_vm(vm_data, current_user)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except InsufficientCreditsError as e:
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
        logger.error(f"VM creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during VM creation"
        )

@router.get("/", response_model=List[VMResponse])
async def get_vms(current_user: UserResponse = Depends(get_current_active_user)):
    """Get all VMs for the current user"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.get_user_vms(current_user.id)
        
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error fetching VMs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch VMs"
        )

@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get a specific VM"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.get_vm(vm_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error fetching VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch VM"
        )

@router.post("/{vm_id}/start", response_model=APIResponse)
async def start_vm(
    vm_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Start a stopped VM"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.start_vm(vm_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
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
        logger.error(f"Error starting VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start VM"
        )

@router.post("/{vm_id}/stop", response_model=APIResponse)
async def stop_vm(
    vm_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Stop a running VM"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.stop_vm(vm_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
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
        logger.error(f"Error stopping VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop VM"
        )

@router.post("/{vm_id}/restart", response_model=APIResponse)
async def restart_vm(
    vm_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Restart a VM (stop then start)"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.restart_vm(vm_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
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
        logger.error(f"Error restarting VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart VM"
        )

@router.delete("/{vm_id}", response_model=APIResponse)
async def delete_vm(
    vm_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete/terminate a VM"""
    try:
        vm_service = service_container.get_vm_service()
        return await vm_service.delete_vm(vm_id, current_user.id)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
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
        logger.error(f"Error deleting VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete VM"
        )

@router.get("/pricing/info",
           summary="Get VM Pricing Information",
           description="Get comprehensive pricing information for all VM instance types",
           response_description="Complete pricing details with specifications and billing information",
           responses={
               200: {
                   "description": "Pricing information retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "pricing": {
                                   "small": 0.05,
                                   "medium": 0.10,
                                   "large": 0.20,
                                   "xlarge": 0.40
                               },
                               "currency": "USD",
                               "billing": "per_hour",
                               "description": "Pricing is charged per hour of usage",
                               "specifications": {
                                   "small": {
                                       "cpu": "1 vCPU",
                                       "ram": "1 GB",
                                       "storage": "20 GB SSD",
                                       "network": "1 Gbps"
                                   },
                                   "medium": {
                                       "cpu": "2 vCPU", 
                                       "ram": "4 GB",
                                       "storage": "40 GB SSD",
                                       "network": "2 Gbps"
                                   },
                                   "large": {
                                       "cpu": "4 vCPU",
                                       "ram": "8 GB", 
                                       "storage": "80 GB SSD",
                                       "network": "4 Gbps"
                                   },
                                   "xlarge": {
                                       "cpu": "8 vCPU",
                                       "ram": "16 GB",
                                       "storage": "160 GB SSD", 
                                       "network": "8 Gbps"
                                   }
                               },
                               "billing_details": {
                                   "minimum_charge": "1 minute",
                                   "billing_increment": "per minute",
                                   "creation_fee": "One-time $0.01 per VM",
                                   "stopped_vm_charge": "$0.00/hour"
                               }
                           }
                       }
                   }
               }
           })
async def get_vm_pricing():
    """
    Get comprehensive VM pricing information.
    
    **Pricing Structure:**
    - **Hourly rates** for running VMs only
    - **No charges** when VMs are stopped
    - **One-time creation fee** per VM
    - **Per-minute billing** with 1-minute minimum
    
    **Instance Types:**
    
    | Type | vCPU | RAM | Storage | Network | Price/Hour |
    |------|------|-----|---------|---------|------------|
    | small | 1 | 1 GB | 20 GB SSD | 1 Gbps | $0.05 |
    | medium | 2 | 4 GB | 40 GB SSD | 2 Gbps | $0.10 |
    | large | 4 | 8 GB | 80 GB SSD | 4 Gbps | $0.20 |
    | xlarge | 8 | 16 GB | 160 GB SSD | 8 Gbps | $0.40 |
    
    **Billing Details:**
    - Charges apply only when VMs are in 'running' state
    - Stopped VMs incur no hourly charges
    - Billing calculated per minute, rounded up
    - Creation fee charged once per VM
    - All prices in USD
    
    **Cost Optimization Tips:**
    - Stop VMs when not in use to avoid charges
    - Choose appropriate instance size for workload
    - Monitor usage via metrics endpoints
    - Use project organization for cost tracking
    
    **No authentication required** - This is a public pricing endpoint.
    """
    from models import INSTANCE_SPECS
    
    # Extract pricing from instance specs
    pricing = {
        instance_type.value: specs["cost_per_hour"] 
        for instance_type, specs in INSTANCE_SPECS.items()
    }
    
    return {
        "pricing": pricing,
        "currency": "USD",
        "billing": "per_hour",
        "description": "Pricing is charged per hour of usage",
        "specifications": {
            instance_type.value: {
                "cpu": specs["cpu"],
                "ram": specs["ram"],
                "storage": specs["storage"]
            }
            for instance_type, specs in INSTANCE_SPECS.items()
        },
        "billing_details": {
            "minimum_charge": "1 minute",
            "billing_increment": "per minute", 
            "creation_fee": "One-time $0.01 per VM",
            "stopped_vm_charge": "$0.00/hour",
            "currency": "USD",
            "tax_inclusive": False
        },
        "cost_optimization": {
            "stop_when_unused": "Stop VMs to avoid hourly charges",
            "right_sizing": "Choose appropriate instance type for workload",
            "monitoring": "Use /vms/{id}/metrics to track usage",
            "project_tracking": "Organize VMs in projects for cost visibility"
        }
    }