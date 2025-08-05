"""
API versioning and compatibility endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from models import APIResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["API Versioning"])

# API version information
API_VERSIONS = {
    "1.0.0": {
        "status": "current",
        "release_date": "2024-01-15",
        "description": "Initial release with full feature set",
        "breaking_changes": [],
        "deprecated_features": [],
        "new_features": [
            "JWT Authentication system",
            "Project management",
            "VM lifecycle management", 
            "Real-time monitoring",
            "Credit-based billing",
            "Comprehensive API documentation"
        ],
        "supported_until": "2025-01-15"
    }
}

CURRENT_VERSION = "1.0.0"
SUPPORTED_VERSIONS = ["1.0.0"]

@router.get("/version",
           summary="Get Current API Version",
           description="Get current API version information and compatibility details",
           response_description="Current API version with detailed information",
           responses={
               200: {
                   "description": "Version information retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "current_version": "1.0.0",
                               "api_status": "stable",
                               "release_date": "2024-01-15",
                               "supported_versions": ["1.0.0"],
                               "deprecation_notices": [],
                               "upgrade_path": None,
                               "compatibility": {
                                   "backwards_compatible": True,
                                   "breaking_changes_in_next": False
                               }
                           }
                       }
                   }
               }
           })
async def get_current_version():
    """
    Get current API version information.
    
    This endpoint provides:
    - Current API version number
    - Release information and status
    - Supported version list
    - Compatibility information
    - Deprecation notices if any
    
    **No authentication required** - This is a public endpoint for version discovery.
    """
    current_info = API_VERSIONS.get(CURRENT_VERSION, {})
    
    return {
        "current_version": CURRENT_VERSION,
        "api_status": "stable",
        "release_date": current_info.get("release_date"),
        "description": current_info.get("description"),
        "supported_versions": SUPPORTED_VERSIONS,
        "deprecation_notices": [],
        "upgrade_path": None,
        "compatibility": {
            "backwards_compatible": True,
            "breaking_changes_in_next": False
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/versions",
           summary="List All API Versions", 
           description="Get information about all API versions including deprecated ones",
           response_description="Complete list of API versions with their status",
           responses={
               200: {
                   "description": "Version list retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "versions": {
                                   "1.0.0": {
                                       "status": "current",
                                       "release_date": "2024-01-15",
                                       "description": "Initial release",
                                       "supported_until": "2025-01-15"
                                   }
                               },
                               "current_version": "1.0.0",
                               "total_versions": 1,
                               "deprecated_count": 0
                           }
                       }
                   }
               }
           })
async def list_all_versions():
    """
    List all API versions with their status and information.
    
    This endpoint provides:
    - Complete version history
    - Status of each version (current, deprecated, unsupported)
    - Release dates and support timelines
    - Feature changes between versions
    
    **Use this endpoint for:**
    - Version planning and migration
    - Understanding API evolution
    - Checking support timelines
    
    **No authentication required** - This is a public endpoint for version discovery.
    """
    deprecated_count = sum(1 for v in API_VERSIONS.values() if v.get("status") == "deprecated")
    
    return {
        "versions": API_VERSIONS,
        "current_version": CURRENT_VERSION,
        "total_versions": len(API_VERSIONS),
        "deprecated_count": deprecated_count,
        "supported_versions": SUPPORTED_VERSIONS,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/version/{version}",
           summary="Get Specific Version Information",
           description="Get detailed information about a specific API version",
           response_description="Detailed information about the requested version",
           responses={
               200: {
                   "description": "Version information retrieved successfully"
               },
               404: {
                   "description": "Version not found",
                   "content": {
                       "application/json": {
                           "example": {
                               "success": False,
                               "message": "API version not found",
                               "available_versions": ["1.0.0"]
                           }
                       }
                   }
               }
           })
async def get_version_info(version: str = Path(..., description="The API version number to get information about (e.g., '1.0.0')")):
    """
    Get detailed information about a specific API version.
    
    **Path Parameters:**
    - `version`: The version number to get information about (e.g., "1.0.0")
    
    This endpoint provides:
    - Version status and support information
    - Release notes and feature changes
    - Breaking changes and migration notes
    - Support timeline and deprecation dates
    
    **No authentication required** - This is a public endpoint for version discovery.
    """
    if version not in API_VERSIONS:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"API version {version} not found",
                "available_versions": list(API_VERSIONS.keys())
            }
        )
    
    version_info = API_VERSIONS[version].copy()
    version_info["version"] = version
    version_info["is_current"] = version == CURRENT_VERSION
    version_info["is_supported"] = version in SUPPORTED_VERSIONS
    version_info["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    return version_info

@router.get("/compatibility",
           summary="Check API Compatibility",
           description="Check compatibility between different API versions and identify breaking changes or migration requirements",
           response_description="Compatibility information between versions",
           responses={
               200: {
                   "description": "Compatibility check completed successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "from_version": "1.0.0",
                               "to_version": "1.0.0", 
                               "compatible": True,
                               "breaking_changes": [],
                               "migration_required": False,
                               "migration_guide": None
                           }
                       }
                   }
               }
           })
async def check_compatibility(
    from_version: str = Query(..., description="Source version to check from"),
    to_version: str = Query(..., description="Target version to check to")
):
    """
    Check compatibility between two API versions.
    
    **Query Parameters:**
    - `from_version`: The version you're currently using
    - `to_version`: The version you want to upgrade to
    
    This endpoint provides:
    - Compatibility status between versions
    - List of breaking changes
    - Migration requirements and guidance
    - Feature differences
    
    **Use this endpoint for:**
    - Planning version upgrades
    - Understanding migration requirements
    - Checking for breaking changes
    
    **No authentication required** - This is a public endpoint for compatibility checking.
    """
    # Validate versions exist
    if from_version not in API_VERSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Source version {from_version} not found"
        )
    
    if to_version not in API_VERSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Target version {to_version} not found"
        )
    
    from_info = API_VERSIONS[from_version]
    to_info = API_VERSIONS[to_version]
    
    # For now, since we only have one version, everything is compatible
    compatible = True
    breaking_changes = []
    migration_required = False
    
    # In future versions, this would contain actual compatibility logic
    if from_version != to_version:
        # Would check for breaking changes between versions
        breaking_changes = to_info.get("breaking_changes", [])
        migration_required = len(breaking_changes) > 0
        compatible = len(breaking_changes) == 0
    
    return {
        "from_version": from_version,
        "to_version": to_version,
        "compatible": compatible,
        "breaking_changes": breaking_changes,
        "migration_required": migration_required,
        "migration_guide": f"/docs/migration/{from_version}-to-{to_version}" if migration_required else None,
        "feature_differences": {
            "added": to_info.get("new_features", []),
            "removed": to_info.get("removed_features", []),
            "deprecated": to_info.get("deprecated_features", [])
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/changelog",
           summary="Get API Changelog",
           description="Get comprehensive changelog information for API versions including version history, breaking changes, new features, bug fixes, and deprecation notices. This endpoint provides detailed information about API evolution and helps developers understand version differences and migration requirements.",
           response_description="Changelog entries for API versions",
           responses={
               200: {
                   "description": "Changelog retrieved successfully",
                   "content": {
                       "application/json": {
                           "example": {
                               "changelog": [
                                   {
                                       "version": "1.0.0",
                                       "release_date": "2024-01-15",
                                       "type": "major",
                                       "changes": {
                                           "added": ["Initial API release"],
                                           "changed": [],
                                           "deprecated": [],
                                           "removed": [],
                                           "fixed": [],
                                           "security": []
                                       }
                                   }
                               ]
                           }
                       }
                   }
               }
           })
async def get_changelog(
    limit: int = Query(10, ge=1, le=50, description="Number of changelog entries to return"),
    version: Optional[str] = Query(None, description="Filter by specific version")
):
    """
    Get API changelog information.
    
    **Query Parameters:**
    - `limit`: Maximum number of changelog entries to return (1-50, default: 10)
    - `version`: Filter changelog for a specific version (optional)
    
    This endpoint provides:
    - Version release history
    - Feature additions and changes
    - Bug fixes and security updates
    - Breaking changes and deprecations
    
    **Changelog follows semantic versioning:**
    - **Added**: New features
    - **Changed**: Changes in existing functionality
    - **Deprecated**: Soon-to-be removed features
    - **Removed**: Features removed in this version
    - **Fixed**: Bug fixes
    - **Security**: Security vulnerability fixes
    
    **No authentication required** - This is a public endpoint for changelog access.
    """
    changelog_entries = []
    
    for ver, info in API_VERSIONS.items():
        if version and ver != version:
            continue
            
        entry = {
            "version": ver,
            "release_date": info.get("release_date"),
            "type": "major" if ver.endswith(".0.0") else "minor" if ver.split(".")[2] == "0" else "patch",
            "description": info.get("description"),
            "changes": {
                "added": info.get("new_features", []),
                "changed": info.get("changed_features", []),
                "deprecated": info.get("deprecated_features", []),
                "removed": info.get("removed_features", []),
                "fixed": info.get("bug_fixes", []),
                "security": info.get("security_fixes", [])
            },
            "breaking_changes": info.get("breaking_changes", []),
            "migration_notes": info.get("migration_notes", [])
        }
        changelog_entries.append(entry)
    
    # Sort by version (newest first)
    changelog_entries.sort(key=lambda x: x["version"], reverse=True)
    
    # Apply limit
    changelog_entries = changelog_entries[:limit]
    
    return {
        "changelog": changelog_entries,
        "total_entries": len(changelog_entries),
        "filtered_by_version": version,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.post("/deprecation-notice",
            summary="Report Deprecated Feature Usage",
            description="Report usage of deprecated API features for tracking",
            response_model=APIResponse,
            responses={
                200: {
                    "description": "Deprecation notice recorded successfully"
                },
                400: {
                    "description": "Invalid deprecation report"
                }
            })
async def report_deprecated_usage(
    feature: str = Query(..., description="Name of the deprecated feature used"),
    version: str = Query(..., description="API version being used"),
    client_info: Optional[str] = Query(None, description="Client application information")
):
    """
    Report usage of deprecated API features.
    
    **Query Parameters:**
    - `feature`: Name of the deprecated feature that was used
    - `version`: API version being used by the client
    - `client_info`: Optional client application information for tracking
    
    This endpoint helps:
    - Track usage of deprecated features
    - Plan deprecation timelines
    - Provide migration assistance
    - Monitor API adoption patterns
    
    **Use this endpoint when:**
    - Your client detects deprecated feature usage
    - You want to track migration progress
    - You need deprecation usage statistics
    
    **No authentication required** - This is a public reporting endpoint.
    """
    # Log the deprecation usage for tracking
    logger.info(f"Deprecated feature usage reported: {feature} in version {version} by {client_info}")
    
    # In a real implementation, this would store the report in a database
    # for analytics and migration planning
    
    return APIResponse(
        success=True,
        message=f"Deprecation notice recorded for feature '{feature}' in version {version}",
        data={
            "feature": feature,
            "version": version,
            "client_info": client_info,
            "recorded_at": datetime.utcnow().isoformat() + "Z",
            "migration_guide": f"/docs/migration/{feature}",
            "support_contact": "api-support@zentrycloud.com"
        }
    )