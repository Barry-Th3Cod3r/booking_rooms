"""
Classroom schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ClassroomBase(BaseModel):
    """Base classroom schema with common fields."""
    name: str = Field(..., min_length=2, max_length=100, description="Classroom name")
    code: str = Field(..., min_length=2, max_length=20, description="Classroom code")
    capacity: int = Field(..., gt=0, description="Maximum capacity")
    description: Optional[str] = Field(None, description="Classroom description")
    location: Optional[str] = Field(None, max_length=200, description="Physical location")
    floor: Optional[int] = Field(None, ge=0, le=20, description="Floor number")
    building: Optional[str] = Field(None, max_length=100, description="Building name")
    equipment: Optional[Dict[str, Any]] = Field(None, description="Available equipment")


class ClassroomCreate(ClassroomBase):
    """Schema for creating a new classroom."""
    pass


class ClassroomUpdate(BaseModel):
    """Schema for updating classroom information."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    capacity: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    floor: Optional[int] = Field(None, ge=0, le=20)
    building: Optional[str] = Field(None, max_length=100)
    equipment: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ClassroomResponse(ClassroomBase):
    """Schema for classroom response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClassroomWithBookings(ClassroomResponse):
    """Extended classroom schema with booking information."""
    bookings: List["BookingResponse"] = []
    
    class Config:
        from_attributes = True

