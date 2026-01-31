"""
Classroom management API routes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse
from app.services.classroom_service import ClassroomService

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


@router.get("/", response_model=List[ClassroomResponse], summary="Get Classrooms")
async def get_classrooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Return only active classrooms"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClassroomResponse]:
    """
    Get list of classrooms.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Whether to return only active classrooms
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ClassroomResponse]: List of classrooms
    """
    classroom_service = ClassroomService(db)
    classrooms = await classroom_service.get_classrooms(
        skip=skip, 
        limit=limit, 
        active_only=active_only
    )
    return [ClassroomResponse.model_validate(classroom) for classroom in classrooms]


@router.get("/{classroom_id}", response_model=ClassroomResponse, summary="Get Classroom by ID")
async def get_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ClassroomResponse:
    """
    Get classroom by ID.
    
    Args:
        classroom_id: Classroom ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ClassroomResponse: Classroom information
        
    Raises:
        HTTPException: If classroom not found
    """
    classroom_service = ClassroomService(db)
    classroom = await classroom_service.get_classroom_by_id(classroom_id)
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    return ClassroomResponse.model_validate(classroom)


@router.post("/", response_model=ClassroomResponse, summary="Create Classroom")
async def create_classroom(
    classroom_create: ClassroomCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ClassroomResponse:
    """
    Create a new classroom (admin only).
    
    Args:
        classroom_create: Classroom creation data
        current_user: Current admin user
        db: Database session
        
    Returns:
        ClassroomResponse: Created classroom
        
    Raises:
        HTTPException: If classroom already exists
    """
    classroom_service = ClassroomService(db)
    
    try:
        classroom = await classroom_service.create_classroom(classroom_create)
        return ClassroomResponse.model_validate(classroom)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{classroom_id}", response_model=ClassroomResponse, summary="Update Classroom")
async def update_classroom(
    classroom_id: int,
    classroom_update: ClassroomUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ClassroomResponse:
    """
    Update classroom information (admin only).
    
    Args:
        classroom_id: Classroom ID
        classroom_update: Classroom update data
        current_user: Current admin user
        db: Database session
        
    Returns:
        ClassroomResponse: Updated classroom information
        
    Raises:
        HTTPException: If classroom not found
    """
    classroom_service = ClassroomService(db)
    
    try:
        classroom = await classroom_service.update_classroom(classroom_id, classroom_update)
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found"
            )
        return ClassroomResponse.model_validate(classroom)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{classroom_id}", summary="Delete Classroom")
async def delete_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a classroom (admin only).
    
    Args:
        classroom_id: Classroom ID
        current_user: Current admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If classroom not found
    """
    classroom_service = ClassroomService(db)
    deleted = await classroom_service.delete_classroom(classroom_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    return {"message": "Classroom deleted successfully"}

