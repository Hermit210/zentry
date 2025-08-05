from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from database import db
from models import TokenData, UserResponse, UserUpdate
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()

# Rate limiting storage (in production, use Redis)
failed_login_attempts: Dict[str, Dict[str, Any]] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating access token"
        )

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiration"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Refresh token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating refresh token"
        )

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check token type for refresh tokens
        if token_type == "refresh" and payload.get("type") != "refresh":
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        return TokenData(email=email)
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None

def check_rate_limit(email: str) -> bool:
    """Check if user is rate limited due to failed login attempts"""
    if email not in failed_login_attempts:
        return True
    
    attempts_data = failed_login_attempts[email]
    if attempts_data["count"] >= MAX_LOGIN_ATTEMPTS:
        if datetime.utcnow() - attempts_data["last_attempt"] < LOCKOUT_DURATION:
            return False
        else:
            # Reset after lockout period
            del failed_login_attempts[email]
    
    return True

def record_failed_login(email: str):
    """Record a failed login attempt"""
    if email not in failed_login_attempts:
        failed_login_attempts[email] = {"count": 0, "last_attempt": datetime.utcnow()}
    
    failed_login_attempts[email]["count"] += 1
    failed_login_attempts[email]["last_attempt"] = datetime.utcnow()

def clear_failed_login(email: str):
    """Clear failed login attempts after successful login"""
    if email in failed_login_attempts:
        del failed_login_attempts[email]

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user from database by email"""
    try:
        if settings.use_in_memory_db:
            memory_store = db.get_memory_store()
            return memory_store["users"].get(email)
        
        supabase = db.get_client()
        if supabase:
            result = supabase.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        
        # Direct PostgreSQL connection
        conn = await db.get_pg_connection()
        if conn:
            result = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            await db.pg_pool.release(conn)
            return dict(result) if result else None
        
        return None
    except Exception as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

async def update_user_profile(user_id: str, updates: UserUpdate) -> Optional[UserResponse]:
    """Update user profile information"""
    try:
        if settings.use_in_memory_db:
            memory_store = db.get_memory_store()
            # Find user by ID in memory store
            for email, user_data in memory_store["users"].items():
                if user_data["id"] == user_id:
                    if updates.name is not None:
                        user_data["name"] = updates.name
                    user_data["updated_at"] = datetime.utcnow().isoformat()
                    return UserResponse(**user_data)
            return None
        
        supabase = db.get_client()
        if supabase:
            update_data = {}
            if updates.name is not None:
                update_data["name"] = updates.name
            
            if update_data:
                result = supabase.table("users").update(update_data).eq("id", user_id).execute()
                if result.data:
                    user_data = result.data[0]
                    return UserResponse(
                        id=user_data["id"],
                        email=user_data["email"],
                        name=user_data["name"],
                        credits=user_data["credits"],
                        created_at=user_data["created_at"],
                        updated_at=user_data.get("updated_at")
                    )
        
        return None
    except Exception as e:
        logger.error(f"Error updating user profile {user_id}: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current authenticated user with comprehensive error handling"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None or token_data.email is None:
            raise credentials_exception
        
        user_data = await get_user_by_email(token_data.email)
        if not user_data:
            raise credentials_exception
        
        # Check if user is active (if we have this field)
        if user_data.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            credits=user_data.get("credits", 0.0),
            created_at=user_data["created_at"],
            updated_at=user_data.get("updated_at"),
            last_login=user_data.get("last_login")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise credentials_exception

async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current active user with additional status checks"""
    # Additional checks can be added here (e.g., subscription status, etc.)
    return current_user

async def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Generate new access token from refresh token"""
    try:
        token_data = verify_token(refresh_token, token_type="refresh")
        if not token_data or not token_data.email:
            return None
        
        # Verify user still exists and is active
        user_data = await get_user_by_email(token_data.email)
        if not user_data or user_data.get("is_active") is False:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user_data["email"]}, 
            expires_delta=access_token_expires
        )
        
        return access_token
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None