"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db, Base
from app.core.config import settings
from app.main import app


# Test database URL (using SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client.
    
    Args:
        db_session: Test database session
        
    Yields:
        AsyncClient: Test HTTP client
    """
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """
    Get authentication headers for testing.
    
    Args:
        client: Test HTTP client
        
    Returns:
        dict: Authorization headers
    """
    # Login with test user
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    return {}


@pytest.fixture
async def test_user_data():
    """Test user data for creating users."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "department": "Test Department",
        "phone": "+34 600 000 000"
    }


@pytest.fixture
async def test_classroom_data():
    """Test classroom data for creating classrooms."""
    return {
        "name": "Test Classroom",
        "code": "TEST1",
        "capacity": 30,
        "description": "Test classroom description",
        "location": "Test location",
        "floor": 1,
        "building": "Test building",
        "equipment": {"projector": True, "whiteboard": True}
    }


@pytest.fixture
async def test_booking_data():
    """Test booking data for creating bookings."""
    from datetime import date, time
    
    return {
        "classroom_id": 1,
        "booking_date": date.today(),
        "start_time": time(9, 0),
        "end_time": time(10, 0),
        "subject": "Test Subject",
        "description": "Test booking description"
    }

