"""
Authentication Models
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ===== Request Models =====
class RegisterRequest(BaseModel):
    """Request to register a new user"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Request to login"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


# ===== Response Models =====
class UserResponse(BaseModel):
    """User data in response"""
    id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    """Authentication response with tokens"""
    success: bool
    data: "AuthData"


class AuthData(BaseModel):
    """Authentication data"""
    user: UserResponse
    access_token: str
    refresh_token: str
    expires_at: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""
    access_token: str
    expires_at: str


# ===== Internal Models =====
class TokenPayload(BaseModel):
    """JWT token payload"""
    user_id: str
    email: str
    exp: int
    iat: int
    type: str  # "access" or "refresh"


class RefreshToken(BaseModel):
    """Stored refresh token"""
    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
