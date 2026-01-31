"""
API routes for the booking rooms application.
"""
from .auth import router as auth_router
from .auth_google import router as auth_google_router
from .users import router as users_router
from .classrooms import router as classrooms_router
from .bookings import router as bookings_router

__all__ = [
    "auth_router", 
    "auth_google_router",
    "users_router", 
    "classrooms_router", 
    "bookings_router"
]


