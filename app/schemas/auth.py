"""
Authentication schemas for JWT tokens and security.
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for JWT token data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = None

