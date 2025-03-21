"""
Authentication utilities for the YouTube Shorts Machine API.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Mock OAuth2 scheme for development
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

class User(BaseModel):
    """User model."""
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True

# Mock user for development
DEV_USER = User(
    id="dev_user",
    username="dev_user",
    email="dev@example.com",
    is_active=True
)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the token.
    
    In production, this would validate the token against a database or auth service.
    For development, it returns a mock user.
    
    Args:
        token: OAuth2 token
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If authentication fails
    """
    # For development, return the mock user if no token is provided
    if token is None:
        logger.debug("No token provided, using development user")
        return DEV_USER
    
    # In production, this would validate the token
    # This is a placeholder for demo purposes
    try:
        # Simulate token validation
        if token == "invalid_token":
            raise ValueError("Invalid token")
        
        # Return mock user for now
        return DEV_USER
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Get the current user from the token, but don't require authentication.
    
    Args:
        token: OAuth2 token
        
    Returns:
        Optional[User]: The current user or None if not authenticated
    """
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def verify_user_session(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Verify the user session and return user info.
    
    Args:
        token: OAuth2 token
        
    Returns:
        Dict[str, Any]: User session information
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await get_current_user(token)
    
    # Return user info in a format suitable for the licensing system
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "session_valid": True
    } 