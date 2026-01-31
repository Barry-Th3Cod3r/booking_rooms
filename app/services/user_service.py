"""
User service for managing user operations.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for handling user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User if found
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username or email.
        
        Args:
            username: Username or email
            
        Returns:
            Optional[User]: User if found
        """
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get list of users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of users
        """
        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            User: Created user
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_username(user_create.username)
        if existing_user:
            raise ValueError("Username already exists")
        
        existing_email = await self.get_user_by_username(user_create.email)
        if existing_email:
            raise ValueError("Email already exists")
        
        # Create new user
        from app.core.security import get_password_hash
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
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_update: User update data
            
        Returns:
            Optional[User]: Updated user if found
        """
        # Get existing user
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check for conflicts if updating username or email
        if user_update.username and user_update.username != user.username:
            existing_user = await self.get_user_by_username(user_update.username)
            if existing_user:
                raise ValueError("Username already exists")
        
        if user_update.email and user_update.email != user.email:
            existing_email = await self.get_user_by_username(user_update.email)
            if existing_email:
                raise ValueError("Email already exists")
        
        # Update user
        update_data = user_update.model_dump(exclude_unset=True)
        stmt = update(User).where(User.id == user_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated user
        return await self.get_user_by_id(user_id)
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if user was deleted
        """
        stmt = delete(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_user_with_bookings(self, user_id: int) -> Optional[User]:
        """
        Get user with their bookings.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User with bookings if found
        """
        stmt = select(User).options(selectinload(User.bookings)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

