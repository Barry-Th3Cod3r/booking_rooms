"""
Booking service for managing booking operations.
Updated to work with PostgreSQL TSTZRANGE for time ranges.
"""
from datetime import date, time, datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, text
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from asyncpg import Range

from app.models.booking import Booking
from app.models.classroom import Classroom
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingUpdate, BookingQuery, BookingAvailability


class BookingService:
    """Service for handling booking operations using PostgreSQL TSTZRANGE."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def create_time_range(start: datetime, end: datetime) -> Range:
        """
        Create a PostgreSQL TSTZRANGE from start and end datetimes.
        Uses '[)' bounds: inclusive start, exclusive end.
        """
        # Ensure timezone-aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return Range(start, end, lower_inc=True, upper_inc=False)
    
    async def get_booking_by_id(self, booking_id: int) -> Optional[Booking]:
        """
        Get booking by ID.
        
        Args:
            booking_id: Booking ID
            
        Returns:
            Optional[Booking]: Booking if found
        """
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_bookings(self, query: BookingQuery) -> List[Booking]:
        """
        Get list of bookings with filters.
        
        Args:
            query: Booking query parameters
            
        Returns:
            List[Booking]: List of bookings
        """
        stmt = select(Booking)
        
        # Apply filters
        conditions = []
        
        if query.classroom_id:
            conditions.append(Booking.classroom_id == query.classroom_id)
        
        if query.user_id:
            conditions.append(Booking.user_id == query.user_id)
        
        if query.start_date:
            # Filter by time range overlapping or after start_date
            start_datetime = datetime.combine(query.start_date, time.min, tzinfo=timezone.utc)
            conditions.append(
                text("upper(time_range) >= :start_dt").bindparams(start_dt=start_datetime)
            )
        
        if query.end_date:
            # Filter by time range overlapping or before end_date
            end_datetime = datetime.combine(query.end_date, time.max, tzinfo=timezone.utc)
            conditions.append(
                text("lower(time_range) <= :end_dt").bindparams(end_dt=end_datetime)
            )
        
        if query.status:
            conditions.append(Booking.status == query.status)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination
        stmt = stmt.offset(query.offset).limit(query.limit)
        
        # Order by start time
        stmt = stmt.order_by(text("lower(time_range)"))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_booking(self, booking_create: BookingCreate, user_id: int) -> Booking:
        """
        Create a new booking.
        
        The EXCLUDE constraint on the database will prevent overlapping bookings.
        
        Args:
            booking_create: Booking creation data
            user_id: User ID making the booking
            
        Returns:
            Booking: Created booking
            
        Raises:
            ValueError: If booking conflicts or classroom not found
        """
        # Check if classroom exists
        classroom_stmt = select(Classroom).where(Classroom.id == booking_create.classroom_id)
        classroom_result = await self.db.execute(classroom_stmt)
        classroom = classroom_result.scalar_one_or_none()
        
        if not classroom:
            raise ValueError("Classroom not found")
        
        if not classroom.is_active:
            raise ValueError("Classroom is not active")
        
        # Create time range
        time_range = self.create_time_range(
            booking_create.start_datetime,
            booking_create.end_datetime
        )
        
        # Create new booking
        db_booking = Booking(
            classroom_id=booking_create.classroom_id,
            user_id=user_id,
            time_range=time_range,
            subject=booking_create.subject,
            description=booking_create.description,
            is_recurring=booking_create.is_recurring,
            recurring_pattern=booking_create.recurring_pattern,
            recurring_end_date=(
                datetime.combine(booking_create.recurring_end_date, time.min, tzinfo=timezone.utc)
                if booking_create.recurring_end_date else None
            ),
        )
        
        self.db.add(db_booking)
        
        try:
            await self.db.commit()
            await self.db.refresh(db_booking)
            return db_booking
        except IntegrityError as e:
            await self.db.rollback()
            # Check if it's an exclusion constraint violation
            if 'booking_no_overlap_exclusion' in str(e):
                raise ValueError("Booking conflicts with an existing reservation for this classroom")
            raise ValueError(f"Database error: {str(e)}")
    
    async def update_booking(self, booking_id: int, booking_update: BookingUpdate) -> Optional[Booking]:
        """
        Update booking information.
        
        Args:
            booking_id: Booking ID
            booking_update: Booking update data
            
        Returns:
            Optional[Booking]: Updated booking if found
        """
        # Get existing booking
        booking = await self.get_booking_by_id(booking_id)
        if not booking:
            return None
        
        # Prepare update data
        update_data = {}
        
        # Handle time range update
        if booking_update.start_datetime is not None and booking_update.end_datetime is not None:
            update_data['time_range'] = self.create_time_range(
                booking_update.start_datetime,
                booking_update.end_datetime
            )
        elif booking_update.start_datetime is not None:
            # Update only start time, keep original end
            update_data['time_range'] = self.create_time_range(
                booking_update.start_datetime,
                booking.end_datetime
            )
        elif booking_update.end_datetime is not None:
            # Update only end time, keep original start
            update_data['time_range'] = self.create_time_range(
                booking.start_datetime,
                booking_update.end_datetime
            )
        
        # Add other fields
        if booking_update.classroom_id is not None:
            update_data['classroom_id'] = booking_update.classroom_id
        if booking_update.subject is not None:
            update_data['subject'] = booking_update.subject
        if booking_update.description is not None:
            update_data['description'] = booking_update.description
        if booking_update.is_recurring is not None:
            update_data['is_recurring'] = booking_update.is_recurring
        if booking_update.recurring_pattern is not None:
            update_data['recurring_pattern'] = booking_update.recurring_pattern
        if booking_update.recurring_end_date is not None:
            update_data['recurring_end_date'] = datetime.combine(
                booking_update.recurring_end_date, time.min, tzinfo=timezone.utc
            )
        if booking_update.status is not None:
            update_data['status'] = booking_update.status
        
        if not update_data:
            return booking
        
        # Update booking
        try:
            stmt = update(Booking).where(Booking.id == booking_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            return await self.get_booking_by_id(booking_id)
        except IntegrityError as e:
            await self.db.rollback()
            if 'booking_no_overlap_exclusion' in str(e):
                raise ValueError("Updated booking would conflict with an existing reservation")
            raise ValueError(f"Database error: {str(e)}")
    
    async def delete_booking(self, booking_id: int) -> bool:
        """
        Delete a booking.
        
        Args:
            booking_id: Booking ID
            
        Returns:
            bool: True if booking was deleted
        """
        stmt = delete(Booking).where(Booking.id == booking_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def check_availability(self, availability: BookingAvailability) -> BookingAvailability:
        """
        Check if a time slot is available for booking.
        Uses PostgreSQL's && (overlaps) operator for efficient range checking.
        
        Args:
            availability: Availability check parameters
            
        Returns:
            BookingAvailability: Availability result with conflicts
        """
        time_range = self.create_time_range(
            availability.start_datetime,
            availability.end_datetime
        )
        
        # Check for overlapping bookings using && operator
        stmt = select(Booking).where(
            and_(
                Booking.classroom_id == availability.classroom_id,
                Booking.status == "confirmed",
                text("time_range && :check_range").bindparams(check_range=time_range)
            )
        )
        
        result = await self.db.execute(stmt)
        conflicts = result.scalars().all()
        
        from app.schemas.booking import BookingResponse, BookingConflict
        
        availability.is_available = len(conflicts) == 0
        availability.conflicts = [
            BookingConflict(
                existing_booking=BookingResponse.from_orm_model(booking),
                conflict_reason="Time slot overlaps with existing booking"
            )
            for booking in conflicts
        ]
        
        return availability
    
    async def get_user_bookings(self, user_id: int, start_date: Optional[date] = None, 
                              end_date: Optional[date] = None) -> List[Booking]:
        """
        Get bookings for a specific user.
        
        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List[Booking]: User's bookings
        """
        stmt = select(Booking).where(Booking.user_id == user_id)
        
        if start_date:
            start_datetime = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(
                text("upper(time_range) >= :start_dt").bindparams(start_dt=start_datetime)
            )
        
        if end_date:
            end_datetime = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
            stmt = stmt.where(
                text("lower(time_range) <= :end_dt").bindparams(end_dt=end_datetime)
            )
        
        stmt = stmt.order_by(text("lower(time_range)"))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_classroom_bookings(self, classroom_id: int, booking_date: date) -> List[Booking]:
        """
        Get bookings for a specific classroom on a specific date.
        
        Args:
            classroom_id: Classroom ID
            booking_date: Booking date
            
        Returns:
            List[Booking]: Classroom bookings for the date
        """
        start_datetime = datetime.combine(booking_date, time.min, tzinfo=timezone.utc)
        end_datetime = datetime.combine(booking_date, time.max, tzinfo=timezone.utc)
        day_range = self.create_time_range(start_datetime, end_datetime)
        
        stmt = select(Booking).where(
            and_(
                Booking.classroom_id == classroom_id,
                text("time_range && :day_range").bindparams(day_range=day_range)
            )
        ).order_by(text("lower(time_range)"))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
