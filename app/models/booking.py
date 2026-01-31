"""
Booking model for managing classroom reservations.
Uses PostgreSQL TSTZRANGE with EXCLUDE constraint to prevent overlapping bookings at DB level.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSTZRANGE, ExcludeConstraint

from app.core.database import Base


class Booking(Base):
    """
    Booking model for storing classroom reservations.
    
    Uses PostgreSQL TSTZRANGE (timestamp with timezone range) for time_range column.
    EXCLUDE constraint ensures no two bookings can overlap for the same classroom.
    """
    
    __tablename__ = "bookings"
    __table_args__ = (
        # EXCLUDE constraint to prevent overlapping bookings at database level
        # Requires btree_gist extension: CREATE EXTENSION IF NOT EXISTS btree_gist;
        ExcludeConstraint(
            ('classroom_id', '='),
            ('time_range', '&&'),
            name='booking_no_overlap_exclusion',
            using='gist',
            where="status = 'confirmed'"
        ),
        # GiST index for efficient range queries
        Index('ix_bookings_time_range_gist', 'time_range', postgresql_using='gist'),
        Index('ix_bookings_classroom_time', 'classroom_id', 'time_range', postgresql_using='gist'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    classroom_id: Mapped[int] = mapped_column(Integer, ForeignKey("classrooms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time range using PostgreSQL TSTZRANGE (timestamp with timezone range)
    # Format: '[start_datetime, end_datetime)'
    time_range = mapped_column(TSTZRANGE, nullable=False)
    
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_pattern: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # daily, weekly, monthly
    recurring_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")  # confirmed, cancelled, pending
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="bookings")
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    
    @property
    def start_datetime(self) -> Optional[datetime]:
        """Get start datetime from range."""
        if self.time_range:
            return self.time_range.lower
        return None
    
    @property
    def end_datetime(self) -> Optional[datetime]:
        """Get end datetime from range."""
        if self.time_range:
            return self.time_range.upper
        return None
    
    @property
    def booking_date(self):
        """Legacy compatibility: get booking date from time range."""
        if self.start_datetime:
            return self.start_datetime.date()
        return None
    
    @property
    def start_time(self):
        """Legacy compatibility: get start time from time range."""
        if self.start_datetime:
            return self.start_datetime.time()
        return None
    
    @property
    def end_time(self):
        """Legacy compatibility: get end time from time range."""
        if self.end_datetime:
            return self.end_datetime.time()
        return None
    
    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, classroom_id={self.classroom_id}, user_id={self.user_id}, time_range={self.time_range})>"
