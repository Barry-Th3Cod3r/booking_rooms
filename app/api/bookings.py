"""
Booking management API routes.
"""
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.schemas.booking import (
    BookingCreate, BookingUpdate, BookingResponse, BookingQuery,
    BookingAvailability, BookingWithDetails
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=List[BookingResponse], summary="Get Bookings")
async def get_bookings(
    classroom_id: int = Query(None, description="Filter by classroom ID"),
    user_id: int = Query(None, description="Filter by user ID"),
    start_date: date = Query(None, description="Filter by start date"),
    end_date: date = Query(None, description="Filter by end date"),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BookingResponse]:
    """
    Get list of bookings with filters.
    
    Args:
        classroom_id: Filter by classroom ID
        user_id: Filter by user ID
        start_date: Filter by start date
        end_date: Filter by end date
        status: Filter by status
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[BookingResponse]: List of bookings
    """
    # Non-admin users can only see their own bookings
    if not current_user.is_admin and user_id and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Non-admin users can only see their own bookings
    if not current_user.is_admin:
        user_id = current_user.id
    
    query = BookingQuery(
        classroom_id=classroom_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        limit=limit,
        offset=offset
    )
    
    booking_service = BookingService(db)
    bookings = await booking_service.get_bookings(query)
    return [BookingResponse.from_orm_model(booking) for booking in bookings]


@router.get("/{booking_id}", response_model=BookingWithDetails, summary="Get Booking by ID")
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BookingWithDetails:
    """
    Get booking by ID.
    
    Args:
        booking_id: Booking ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingWithDetails: Booking information with details
        
    Raises:
        HTTPException: If booking not found or access denied
    """
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only access their own bookings unless they're admin
    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return BookingWithDetails.from_orm_model(booking)


@router.post("/", response_model=BookingResponse, summary="Create Booking")
async def create_booking(
    booking_create: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """
    Create a new booking.
    
    Args:
        booking_create: Booking creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingResponse: Created booking
        
    Raises:
        HTTPException: If booking conflicts or validation fails
    """
    booking_service = BookingService(db)
    
    try:
        booking = await booking_service.create_booking(booking_create, current_user.id)
        return BookingResponse.from_orm_model(booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{booking_id}", response_model=BookingResponse, summary="Update Booking")
async def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """
    Update booking information.
    
    Args:
        booking_id: Booking ID
        booking_update: Booking update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingResponse: Updated booking information
        
    Raises:
        HTTPException: If booking not found or access denied
    """
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only update their own bookings unless they're admin
    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        updated_booking = await booking_service.update_booking(booking_id, booking_update)
        return BookingResponse.from_orm_model(updated_booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{booking_id}", summary="Delete Booking")
async def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a booking.
    
    Args:
        booking_id: Booking ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If booking not found or access denied
    """
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Users can only delete their own bookings unless they're admin
    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    deleted = await booking_service.delete_booking(booking_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return {"message": "Booking deleted successfully"}


@router.post("/check-availability", response_model=BookingAvailability, summary="Check Booking Availability")
async def check_availability(
    availability: BookingAvailability,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BookingAvailability:
    """
    Check if a time slot is available for booking.
    
    Args:
        availability: Availability check parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingAvailability: Availability result with conflicts
    """
    booking_service = BookingService(db)
    return await booking_service.check_availability(availability)


@router.get("/user/{user_id}", response_model=List[BookingResponse], summary="Get User Bookings")
async def get_user_bookings(
    user_id: int,
    start_date: date = Query(None, description="Filter by start date"),
    end_date: date = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BookingResponse]:
    """
    Get bookings for a specific user.
    
    Args:
        user_id: User ID
        start_date: Filter by start date
        end_date: Filter by end date
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[BookingResponse]: User's bookings
        
    Raises:
        HTTPException: If access denied
    """
    # Users can only see their own bookings unless they're admin
    if not current_user.is_admin and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    booking_service = BookingService(db)
    bookings = await booking_service.get_user_bookings(user_id, start_date, end_date)
    return [BookingResponse.from_orm_model(booking) for booking in bookings]


@router.get("/classroom/{classroom_id}/date/{booking_date}", 
           response_model=List[BookingResponse], 
           summary="Get Classroom Bookings by Date")
async def get_classroom_bookings_by_date(
    classroom_id: int,
    booking_date: date,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BookingResponse]:
    """
    Get bookings for a specific classroom on a specific date.
    
    Args:
        classroom_id: Classroom ID
        booking_date: Booking date
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[BookingResponse]: Classroom bookings for the date
    """
    booking_service = BookingService(db)
    bookings = await booking_service.get_classroom_bookings(classroom_id, booking_date)
    return [BookingResponse.from_orm_model(booking) for booking in bookings]

