from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import timedelta
from database import db
from models import UserSignup, UserLogin, UserUpdate, Token, UserResponse, APIResponse
from auth import verify_password, get_password_hash, create_access_token, get_current_active_user
from services.service_container import service_container
from services.base_service import ServiceError, ValidationError, NotFoundError
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", 
             response_model=Token, 
             status_code=status.HTTP_201_CREATED,
             summary="User Registration",
             description="Register a new user account with email and password",
             response_description="JWT token and user information for the newly created account",
             responses={
                 201: {
                     "description": "User account created successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                 "expires_in": 3600,
                                 "user": {
                                     "id": "123e4567-e89b-12d3-a456-426614174000",
                                     "email": "user@example.com",
                                     "name": "John Doe",
                                     "credits": 50.0,
                                     "created_at": "2024-01-15T10:30:00Z"
                                 }
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Registration failed - validation error or email already exists",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Email already registered"
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation error in request data",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                     {
                                         "loc": ["body", "email"],
                                         "msg": "field required",
                                         "type": "value_error.missing"
                                     }
                                 ]
                             }
                         }
                     }
                 }
             })
async def signup(user_data: UserSignup):
    """
    Register a new user account.
    
    **Features:**
    - Creates a new user with email and password
    - Provides 50 welcome credits automatically
    - Returns JWT token for immediate use
    - Validates email format and password strength
    
    **Requirements:**
    - Unique email address (not already registered)
    - Password minimum 8 characters with letters and numbers
    - Valid name (2-100 characters, letters/spaces/hyphens/apostrophes only)
    
    **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "name": "John Doe", 
        "password": "securepassword123"
    }
    ```
    
    **Response:**
    - JWT access token (expires in 60 minutes by default)
    - Complete user profile information
    - Account creation timestamp
    
    **Usage:**
    Use the returned token in subsequent requests:
    ```
    Authorization: Bearer your_access_token_here
    ```
    
    **Rate Limit:** 5 requests per minute per IP address
    """
    try:
        auth_service = service_container.get_auth_service()
        return await auth_service.signup(user_data)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ServiceError as e:
        if e.error_code == "USER_CREATION_FAILED":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.message
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@router.post("/login", 
             response_model=Token,
             summary="User Authentication",
             description="Authenticate user credentials and return JWT access token",
             response_description="JWT token and user information for authenticated user",
             responses={
                 200: {
                     "description": "Authentication successful",
                     "content": {
                         "application/json": {
                             "example": {
                                 "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                 "expires_in": 3600,
                                 "user": {
                                     "id": "123e4567-e89b-12d3-a456-426614174000",
                                     "email": "user@example.com",
                                     "name": "John Doe",
                                     "credits": 45.25,
                                     "created_at": "2024-01-15T10:30:00Z",
                                     "updated_at": "2024-01-15T12:15:00Z"
                                 }
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Authentication failed - invalid credentials",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Invalid email or password"
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation error in request data"
                 }
             })
async def login(user_data: UserLogin):
    """
    Authenticate user and return access token.
    
    **Process:**
    1. Validates user credentials against database
    2. Generates JWT access token with configurable expiration
    3. Returns user profile information with current credit balance
    4. Updates last login timestamp
    
    **Security Features:**
    - Secure password verification using bcrypt
    - JWT tokens with expiration
    - Rate limiting to prevent brute force attacks
    - Account lockout after multiple failed attempts (future feature)
    
    **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    ```
    
    **Token Usage:**
    Include the returned token in the Authorization header for protected endpoints:
    ```
    Authorization: Bearer your_access_token_here
    ```
    
    **Token Expiration:**
    - Default expiration: 60 minutes
    - Configurable via environment settings
    - Use `/auth/refresh` endpoint to renew tokens
    
    **Rate Limit:** 5 requests per minute per IP address
    """
    try:
        auth_service = service_container.get_auth_service()
        return await auth_service.login(user_data)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except ServiceError as e:
        if e.error_code == "RATE_LIMITED":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=e.message
            )
        elif e.error_code == "ACCOUNT_DEACTIVATED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.get("/me", 
            response_model=UserResponse,
            summary="Get Current User Profile",
            description="Get current authenticated user's profile information and account details",
            response_description="Complete user profile with current credit balance and statistics",
            responses={
                200: {
                    "description": "User profile retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "email": "user@example.com",
                                "name": "John Doe",
                                "credits": 45.25,
                                "total_spent": 4.75,
                                "vm_count": 3,
                                "project_count": 2,
                                "active_vm_count": 1,
                                "is_active": True,
                                "role": "user",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T12:15:00Z",
                                "last_login": "2024-01-15T14:20:00Z"
                            }
                        }
                    }
                },
                401: {
                    "description": "Authentication required - invalid or missing token",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Not authenticated"
                            }
                        }
                    }
                },
                404: {
                    "description": "User not found - token valid but user doesn't exist"
                }
            })
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Get current authenticated user's profile information.
    
    **Returns:**
    - Complete user profile details
    - Current credit balance and spending history
    - Account statistics (VM count, project count, etc.)
    - Account status and role information
    - Registration and last login timestamps
    
    **Authentication:**
    Requires valid JWT token in Authorization header:
    ```
    Authorization: Bearer your_access_token_here
    ```
    
    **Use Cases:**
    - Display user profile in applications
    - Check current credit balance before operations
    - Verify account status and permissions
    - Show account statistics and usage
    
    **Profile Information Includes:**
    - **Basic Info**: ID, email, name, role
    - **Credits**: Current balance and total spent
    - **Resources**: VM count, project count, active VMs
    - **Status**: Account active status
    - **Timestamps**: Created, updated, last login
    
    **Rate Limit:** 100 requests per minute per user
    """
    try:
        auth_service = service_container.get_auth_service()
        return await auth_service.get_user_profile(current_user.id)
        
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
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/logout", 
             response_model=APIResponse,
             summary="User Logout",
             description="Logout user by invalidating client-side token",
             response_description="Logout confirmation message",
             responses={
                 200: {
                     "description": "Logout successful",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": True,
                                 "message": "Successfully logged out. Please remove the token from client storage."
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Authentication required - invalid or missing token"
                 }
             })
async def logout():
    """
    Logout user by invalidating client-side token.
    
    **Process:**
    - Instructs client to remove JWT token from storage
    - In a production system, this would also invalidate the token server-side
    - Provides confirmation of successful logout
    
    **Client Implementation:**
    After receiving successful response, remove the token from:
    - Local storage
    - Session storage  
    - Memory/state management
    - HTTP-only cookies (if used)
    
    **Security Notes:**
    - JWT tokens are stateless, so server-side invalidation requires additional infrastructure
    - Consider implementing token blacklisting for enhanced security
    - Use short token expiration times to minimize exposure
    
    **Authentication:** Requires valid JWT token (optional for logout)
    
    **Rate Limit:** 10 requests per minute per user
    """
    return APIResponse(
        success=True,
        message="Successfully logged out. Please remove the token from client storage."
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    updates: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update user profile information"""
    try:
        from auth import update_user_profile
        
        updated_user = await update_user_profile(current_user.id, updates)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during profile update"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Query(..., description="The refresh token obtained during login to generate a new access token")):
    """Refresh access token using refresh token"""
    try:
        from auth import refresh_access_token, get_user_by_email
        
        new_access_token = await refresh_access_token(refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user data for response
        from auth import verify_token
        token_data = verify_token(refresh_token, token_type="refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_data = await get_user_by_email(token_data.email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user_response = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            credits=user_data["credits"],
            created_at=user_data["created_at"],
            updated_at=user_data.get("updated_at")
        )
        
        return Token(
            access_token=new_access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )