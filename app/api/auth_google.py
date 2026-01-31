"""
Google OAuth authentication endpoint.
Validates Google ID tokens and issues internal JWT tokens.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_google_token, 
    create_access_token, 
    create_refresh_token,
    get_password_hash
)
from app.core.config import settings
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleToken(BaseModel):
    """Schema for Google OAuth token."""
    id_token: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user info in auth response."""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_admin: bool = False
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Combined auth response with tokens and user info."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


async def get_or_create_user_from_google(
    db: AsyncSession, 
    google_user: dict
) -> User:
    """
    Get existing user by email or create new user from Google OAuth data.
    
    Args:
        db: Database session
        google_user: User info from Google token verification
        
    Returns:
        User: Existing or newly created user
    """
    # Try to find existing user by email
    stmt = select(User).where(User.email == google_user["email"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info from Google if needed
        if not user.full_name and google_user.get("name"):
            user.full_name = google_user["name"]
            await db.commit()
        return user
    
    # Create new user from Google data
    # Generate a username from email (part before @)
    email_username = google_user["email"].split("@")[0]
    
    # Check if username exists, append number if needed
    base_username = email_username
    counter = 1
    while True:
        stmt = select(User).where(User.username == email_username)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            break
        email_username = f"{base_username}{counter}"
        counter += 1
    
    new_user = User(
        username=email_username,
        email=google_user["email"],
        full_name=google_user.get("name", ""),
        # Google users don't have a password - they use OAuth
        hashed_password=get_password_hash(f"google_oauth_{google_user['google_id']}"),
        is_active=True,
        is_admin=False,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/google", response_model=AuthResponse, summary="Login with Google")
async def google_login(
    google_token: GoogleToken,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Authenticate user with Google OAuth ID token.
    
    This endpoint:
    1. Verifies the Google ID token
    2. Gets or creates a user account based on the Google email
    3. Issues internal JWT access and refresh tokens
    
    Args:
        google_token: Google ID token from frontend OAuth flow
        db: Database session
        
    Returns:
        AuthResponse: Access token, refresh token, and user info
        
    Raises:
        HTTPException: If Google token is invalid or Google OAuth is not configured
    """
    # Check if Google OAuth is configured
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID environment variable."
        )
    
    # Verify Google token and get user info
    google_user = await verify_google_token(google_token.id_token)
    
    # Verify email is verified by Google
    if not google_user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email is not verified"
        )
    
    # Get or create user
    user = await get_or_create_user_from_google(db, google_user)
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Generate our JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh an expired access token using a valid refresh token.
    
    Args:
        request: Refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    from app.core.security import verify_token
    
    payload = verify_token(request.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify user still exists and is active
    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
