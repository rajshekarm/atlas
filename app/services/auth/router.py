"""
Authentication Router
Handles user registration, login, and token refresh
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Optional
import logging
from datetime import datetime

from app.services.auth.models import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    AuthData,
    UserResponse,
    RefreshTokenResponse,
    RefreshToken
)
from app.services.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.services.flash.models import UserProfile, CreateUserProfileRequest


router = APIRouter()
logger = logging.getLogger(__name__)


# In-memory storage (replace with database in production)
users_db: Dict[str, dict] = {}  # email -> user data
refresh_tokens_db: Dict[str, RefreshToken] = {}  # token -> RefreshToken


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """
    Register a new user
    
    This endpoint:
    - Validates email is not already registered
    - Hashes the password
    - Creates user account
    - Generates access and refresh tokens
    - Returns user data and tokens
    """
    try:
        # Check if user already exists
        if request.email in users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Generate user ID
        import uuid
        user_id = f"user_{uuid.uuid4().hex[:10]}"
        
        # Create user
        user_data = {
            "id": user_id,
            "name": request.name,
            "email": request.email,
            "password": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store user
        users_db[request.email] = user_data
        
        # Generate tokens
        access_token, access_expires = create_access_token(user_id, request.email)
        refresh_token, refresh_expires = create_refresh_token(user_id)
        
        # Store refresh token
        refresh_tokens_db[refresh_token] = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            expires_at=refresh_expires
        )
        
        # Create response
        user_response = UserResponse(
            id=user_id,
            name=request.name,
            email=request.email
        )
        
        auth_data = AuthData(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
        logger.info(f"User registered: {request.email}")
        
        return AuthResponse(success=True, data=auth_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login an existing user
    
    This endpoint:
    - Validates email and password
    - Generates new access and refresh tokens
    - Returns user data and tokens
    """
    try:
        # Check if user exists
        if request.email not in users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = users_db[request.email]
        
        # Verify password
        if not verify_password(request.password, user_data["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token, access_expires = create_access_token(
            user_data["id"], 
            request.email
        )
        refresh_token, refresh_expires = create_refresh_token(user_data["id"])
        
        # Store refresh token
        refresh_tokens_db[refresh_token] = RefreshToken(
            token=refresh_token,
            user_id=user_data["id"],
            expires_at=refresh_expires
        )
        
        # Create response
        user_response = UserResponse(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"]
        )
        
        auth_data = AuthData(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
        logger.info(f"User logged in: {request.email}")
        
        return AuthResponse(success=True, data=auth_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    This endpoint:
    - Validates refresh token
    - Generates new access token
    - Returns new access token and expiration
    """
    try:
        # Check if refresh token exists
        if request.refresh_token not in refresh_tokens_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        refresh_token_data = refresh_tokens_db[request.refresh_token]
        
        # Check if refresh token is expired
        if datetime.utcnow() > refresh_token_data.expires_at:
            # Clean up expired token
            del refresh_tokens_db[request.refresh_token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Get user data
        user_id = refresh_token_data.user_id
        user_email = None
        
        # Find user email
        for email, user_data in users_db.items():
            if user_data["id"] == user_id:
                user_email = email
                break
        
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new access token
        access_token, access_expires = create_access_token(user_id, user_email)
        
        logger.info(f"Token refreshed for user: {user_id}")
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    """
    Logout user by invalidating refresh token
    
    This endpoint:
    - Invalidates the provided refresh token
    - Returns success message
    """
    try:
        # Remove refresh token if it exists
        if request.refresh_token in refresh_tokens_db:
            del refresh_tokens_db[request.refresh_token]
            logger.info(f"User logged out")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = None):
    """
    Get current user information from access token
    
    This endpoint:
    - Validates access token
    - Returns user information
    
    Note: In production, use proper authentication dependency
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = authorization.replace("Bearer ", "")
        
        from app.services.auth.utils import verify_access_token
        payload = verify_access_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Find user
        email = payload.get("email")
        if email not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = users_db[email]
        
        return UserResponse(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
