"""
Booking schemas for request/response validation.
Updated to support TSTZRANGE model with legacy compatibility.
"""
from datetime import datetime, date, time, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


class BookingBase(BaseModel):
    """Base booking schema with common fields."""
    classroom_id: int = Field(..., description="Classroom ID")
    # Accept either datetime range directly or legacy date/time fields
    start_datetime: Optional[datetime] = Field(None, description="Start datetime (ISO format)")
    end_datetime: Optional[datetime] = Field(None, description="End datetime (ISO format)")
    # Legacy fields for backward compatibility
    booking_date: Optional[date] = Field(None, description="Booking date (legacy)")
    start_time: Optional[time] = Field(None, description="Start time (legacy)")
    end_time: Optional[time] = Field(None, description="End time (legacy)")
    subject: Optional[str] = Field(None, max_length=200, description="Subject or course")
    description: Optional[str] = Field(None, description="Additional description")
    is_recurring: bool = Field(False, description="Is this a recurring booking")
    recurring_pattern: Optional[str] = Field(None, max_length=50, description="Recurring pattern")
    recurring_end_date: Optional[date] = Field(None, description="End date for recurring bookings")

    @model_validator(mode='after')
    def validate_time_fields(self):
        """Ensure we have valid time range either via new or legacy fields."""
        has_new_format = self.start_datetime is not None and self.end_datetime is not None
        has_legacy_format = (
            self.booking_date is not None and 
            self.start_time is not None and 
            self.end_time is not None
        )
        
        if not has_new_format and not has_legacy_format:
            raise ValueError(
                "Must provide either (start_datetime, end_datetime) or "
                "(booking_date, start_time, end_time)"
            )
        
        # Convert legacy format to new format if needed
        if has_legacy_format and not has_new_format:
            self.start_datetime = datetime.combine(
                self.booking_date, self.start_time, tzinfo=timezone.utc
            )
            self.end_datetime = datetime.combine(
                self.booking_date, self.end_time, tzinfo=timezone.utc
            )
        
        # Validate time order
        if self.start_datetime >= self.end_datetime:
            raise ValueError("Start time must be before end time")
        
        return self


class BookingCreate(BookingBase):
    """Schema for creating a new booking."""
    pass


class BookingUpdate(BaseModel):
    """Schema for updating booking information."""
    classroom_id: Optional[int] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    # Legacy fields
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    subject: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurring_pattern: Optional[str] = Field(None, max_length=50)
    recurring_end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)

    @model_validator(mode='after')
    def validate_time_update(self):
        """Validate time fields if updating time range."""
        # If updating legacy fields, convert to new format
        if self.booking_date is not None and self.start_time is not None and self.end_time is not None:
            self.start_datetime = datetime.combine(
                self.booking_date, self.start_time, tzinfo=timezone.utc
            )
            self.end_datetime = datetime.combine(
                self.booking_date, self.end_time, tzinfo=timezone.utc
            )
        
        # Validate time order if both provided
        if self.start_datetime is not None and self.end_datetime is not None:
            if self.start_datetime >= self.end_datetime:
                raise ValueError("Start time must be before end time")
        
        return self


class BookingResponse(BaseModel):
    """Schema for booking response."""
    id: int
    classroom_id: int
    user_id: int
    start_datetime: datetime = Field(..., description="Start datetime")
    end_datetime: datetime = Field(..., description="End datetime")
    # Include legacy fields for backward compatibility
    booking_date: date = Field(..., description="Booking date")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    subject: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None
    recurring_end_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, booking):
        """Create response from ORM model with time_range."""
        return cls(
            id=booking.id,
            classroom_id=booking.classroom_id,
            user_id=booking.user_id,
            start_datetime=booking.start_datetime,
            end_datetime=booking.end_datetime,
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            subject=booking.subject,
            description=booking.description,
            is_recurring=booking.is_recurring,
            recurring_pattern=booking.recurring_pattern,
            recurring_end_date=booking.recurring_end_date.date() if booking.recurring_end_date else None,
            status=booking.status,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
        )


class BookingWithDetails(BookingResponse):
    """Extended booking schema with related information."""
    classroom: "ClassroomResponse"
    user: "UserResponse"
    
    class Config:
        from_attributes = True


class BookingQuery(BaseModel):
    """Schema for querying bookings."""
    classroom_id: Optional[int] = None
    user_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class BookingConflict(BaseModel):
    """Schema for booking conflict information."""
    existing_booking: BookingResponse
    conflict_reason: str


class BookingAvailability(BaseModel):
    """Schema for checking booking availability."""
    classroom_id: int
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    # Legacy fields
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: bool = False
    conflicts: List[BookingConflict] = []

    @model_validator(mode='after')
    def validate_availability_time(self):
        """Convert legacy fields to datetime if needed."""
        if self.booking_date and self.start_time and self.end_time:
            if self.start_datetime is None:
                self.start_datetime = datetime.combine(
                    self.booking_date, self.start_time, tzinfo=timezone.utc
                )
            if self.end_datetime is None:
                self.end_datetime = datetime.combine(
                    self.booking_date, self.end_time, tzinfo=timezone.utc
                )
        return self
