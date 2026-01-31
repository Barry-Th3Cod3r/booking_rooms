"""
Pydantic schemas for request/response validation.
"""
from .user import UserCreate, UserUpdate, UserResponse, UserLogin
from .classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse
from .booking import BookingCreate, BookingUpdate, BookingResponse, BookingQuery
from .auth import Token, TokenData

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "ClassroomCreate", "ClassroomUpdate", "ClassroomResponse",
    "BookingCreate", "BookingUpdate", "BookingResponse", "BookingQuery",
    "Token", "TokenData"
]

