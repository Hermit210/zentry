from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from database import db
from models import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithVMs, UserResponse, APIResponse, VMResponse
from auth import get_current_active_user
from services.service_container import service_container
from services.base_service import ServiceError, ValidationError, NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Create a new project"""
    try:
        project_service = service_container.get_project_service()
        return await project_service.create_project(project_data, current_user.id)
        
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
        logger.error(f"Project creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during project creation"
        )

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(current_user: UserResponse = Depends(get_current_active_user)):
    """Get all projects for the current user"""
    try:
        project_service = service_container.get_project_service()
        return await project_service.get_user_projects(current_user.id)
        
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )

@router.get("/{project_id}", response_model=ProjectWithVMs)
async def get_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get a specific project with its VMs"""
    try:
        project_service = service_container.get_project_service()
        return await project_service.get_project(project_id, current_user.id, include_vms=True)
        
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
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update a project"""
    try:
        project_service = service_container.get_project_service()
        return await project_service.update_project(project_id, project_data, current_user.id)
        
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
        logger.error(f"Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )

@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete a project and all its VMs"""
    try:
        project_service = service_container.get_project_service()
        result = await project_service.delete_project(project_id, current_user.id)
        
        return APIResponse(
            success=result["success"],
            message=result["message"]
        )
        
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
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )