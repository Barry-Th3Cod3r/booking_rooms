"""
Classroom service for managing classroom operations.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


class ClassroomService:
    """Service for handling classroom operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_classroom_by_id(self, classroom_id: int) -> Optional[Classroom]:
        """
        Get classroom by ID.
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            Optional[Classroom]: Classroom if found
        """
        stmt = select(Classroom).where(Classroom.id == classroom_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_classroom_by_code(self, code: str) -> Optional[Classroom]:
        """
        Get classroom by code.
        
        Args:
            code: Classroom code
            
        Returns:
            Optional[Classroom]: Classroom if found
        """
        stmt = select(Classroom).where(Classroom.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_classrooms(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Classroom]:
        """
        Get list of classrooms with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active classrooms
            
        Returns:
            List[Classroom]: List of classrooms
        """
        stmt = select(Classroom)
        
        if active_only:
            stmt = stmt.where(Classroom.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_classroom(self, classroom_create: ClassroomCreate) -> Classroom:
        """
        Create a new classroom.
        
        Args:
            classroom_create: Classroom creation data
            
        Returns:
            Classroom: Created classroom
            
        Raises:
            ValueError: If classroom already exists
        """
        # Check if classroom already exists
        existing_name = await self._get_classroom_by_name(classroom_create.name)
        if existing_name:
            raise ValueError("Classroom name already exists")
        
        existing_code = await self.get_classroom_by_code(classroom_create.code)
        if existing_code:
            raise ValueError("Classroom code already exists")
        
        # Create new classroom
        db_classroom = Classroom(**classroom_create.model_dump())
        
        self.db.add(db_classroom)
        await self.db.commit()
        await self.db.refresh(db_classroom)
        
        return db_classroom
    
    async def update_classroom(self, classroom_id: int, classroom_update: ClassroomUpdate) -> Optional[Classroom]:
        """
        Update classroom information.
        
        Args:
            classroom_id: Classroom ID
            classroom_update: Classroom update data
            
        Returns:
            Optional[Classroom]: Updated classroom if found
        """
        # Get existing classroom
        classroom = await self.get_classroom_by_id(classroom_id)
        if not classroom:
            return None
        
        # Check for conflicts if updating name or code
        if classroom_update.name and classroom_update.name != classroom.name:
            existing_name = await self._get_classroom_by_name(classroom_update.name)
            if existing_name:
                raise ValueError("Classroom name already exists")
        
        if classroom_update.code and classroom_update.code != classroom.code:
            existing_code = await self.get_classroom_by_code(classroom_update.code)
            if existing_code:
                raise ValueError("Classroom code already exists")
        
        # Update classroom
        update_data = classroom_update.model_dump(exclude_unset=True)
        stmt = update(Classroom).where(Classroom.id == classroom_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated classroom
        return await self.get_classroom_by_id(classroom_id)
    
    async def delete_classroom(self, classroom_id: int) -> bool:
        """
        Delete a classroom.
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            bool: True if classroom was deleted
        """
        stmt = delete(Classroom).where(Classroom.id == classroom_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_classroom_with_bookings(self, classroom_id: int) -> Optional[Classroom]:
        """
        Get classroom with its bookings.
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            Optional[Classroom]: Classroom with bookings if found
        """
        stmt = select(Classroom).options(selectinload(Classroom.bookings)).where(Classroom.id == classroom_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_classroom_by_name(self, name: str) -> Optional[Classroom]:
        """
        Get classroom by name.
        
        Args:
            name: Classroom name
            
        Returns:
            Optional[Classroom]: Classroom if found
        """
        stmt = select(Classroom).where(Classroom.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

