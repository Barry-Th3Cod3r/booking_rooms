"""
Classroom model for managing available classrooms.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Classroom(Base):
    """Classroom model for storing classroom information."""
    
    __tablename__ = "classrooms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    equipment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Equipment list as JSON
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="classroom", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Classroom(id={self.id}, name='{self.name}', code='{self.code}')>"

