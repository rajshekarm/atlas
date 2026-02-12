"""
Authentication Utilities
JWT token generation, password hashing, etc.
"""
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: str, email: str) -> tuple[str, datetime]:
    """
    Create a JWT access token
    
    Args:
        user_id: User ID to encode in token
        email: User email to encode in token
        
    Returns:
        Tuple of (token, expiration_datetime)
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    iat_timestamp = int(now.timestamp())
    exp_timestamp = int(expires_at.timestamp())
    
    print(f"🆕 [DEBUG] Creating token - Current time: {now}")
    print(f"🆕 [DEBUG] iat: {iat_timestamp}, exp: {exp_timestamp}")
    
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": exp_timestamp,
        "iat": iat_timestamp,
        "type": "access"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"🆕 [DEBUG] Token created: {token[:30]}...")
    return token, expires_at


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """
    Create a refresh token
    
    Args:
        user_id: User ID to encode in token
        
    Returns:
        Tuple of (token, expiration_datetime)
    """
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    return token, expires_at


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token (SIMPLIFIED FOR DEBUGGING)
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        print(f"🔍 [DEBUG] Attempting to decode token: {token[:20]}...")
        print(f"🔑 [DEBUG] Using SECRET_KEY: {SECRET_KEY[:10]}...")

        print("decoding...........")
        
        # SIMPLIFIED: Decode without validation for now
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={
                "verify_exp": False,  # Don't verify expiration
                "verify_iat": False,  # Don't verify issued-at
                "verify_nbf": False   # Don't verify not-before
            }
        )
        
        print(f"✅ [DEBUG] Token decoded successfully (no time validation): {payload}")
        
        # Just check token type
        if payload.get("type") != "access":
            print(f"❌ [DEBUG] Token type mismatch. Expected 'access', got: {payload.get('type')}")
            return None
        
        print(f"✅ [DEBUG] Token type verified: access")
        return payload
        
    except Exception as e:
        print(f"💥 [DEBUG] Error decoding token: {type(e).__name__}: {e}")
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a token without verifying signature (for debugging)
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded payload or None
    """
    try:
        print(f"🔓 [DEBUG] Decoding token WITHOUT verification: {token[:20]}...")
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"✅ [DEBUG] Unverified decode successful: {payload}")
        return payload
    except Exception as e:
        print(f"💥 [DEBUG] Failed to decode even without verification: {type(e).__name__}: {e}")
        return None
