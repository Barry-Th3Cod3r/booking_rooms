"""
Authentication service for user login and token management.
"""
from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import authenticate_user, create_access_token, get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import Token


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def login(self, user_login: UserLogin) -> Optional[Token]:
        """
        Authenticate user and return access token.
        
        Args:
            user_login: User login credentials
            
        Returns:
            Optional[Token]: Access token if authentication successful
            
        Raises:
            HTTPException: If authentication fails
        """
        user = await authenticate_user(
            self.db, 
            user_login.username, 
            user_login.password
        )
        
        if not user:
            return None
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "is_admin": user.is_admin},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def register(self, user_create: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            User: Created user
            
        Raises:
            HTTPException: If user already exists
        """
        # Check if user already exists
        existing_user = await self._get_user_by_username_or_email(
            user_create.username, 
            user_create.email
        )
        
        if existing_user:
            if existing_user.username == user_create.username:
                raise ValueError("Username already registered")
            if existing_user.email == user_create.email:
                raise ValueError("Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            department=user_create.department,
            phone=user_create.phone
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def _get_user_by_username_or_email(self, username: str, email: str) -> Optional[User]:
        """
        Get user by username or email.
        
        Args:
            username: Username
            email: Email address
            
        Returns:
            Optional[User]: User if found
        """
        stmt = select(User).where(
            (User.username == username) | (User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

