"""
Database initialization script with sample data.
"""
import asyncio
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.classroom import Classroom
from app.models.booking import Booking
from app.core.security import get_password_hash


async def init_database():
    """
    Initialize database with sample data.
    """
    async with AsyncSessionLocal() as db:
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@instituto.edu",
            full_name="Administrador del Sistema",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
            department="Administración",
            phone="+34 600 000 000"
        )
        
        # Create sample teachers
        teacher1 = User(
            username="profesor1",
            email="profesor1@instituto.edu",
            full_name="María García López",
            hashed_password=get_password_hash("profesor123"),
            department="Informática",
            phone="+34 600 000 001"
        )
        
        teacher2 = User(
            username="profesor2",
            email="profesor2@instituto.edu",
            full_name="Juan Pérez Martínez",
            hashed_password=get_password_hash("profesor123"),
            department="Matemáticas",
            phone="+34 600 000 002"
        )
        
        teacher3 = User(
            username="profesor3",
            email="profesor3@instituto.edu",
            full_name="Ana Rodríguez Sánchez",
            hashed_password=get_password_hash("profesor123"),
            department="Física",
            phone="+34 600 000 003"
        )
        
        # Add users to database
        db.add_all([admin_user, teacher1, teacher2, teacher3])
        await db.commit()
        
        # Create sample classrooms
        classroom1 = Classroom(
            name="Aula de Informática 1",
            code="INF1",
            capacity=25,
            description="Aula equipada con ordenadores para clases de informática",
            location="Planta baja, edificio A",
            floor=0,
            building="Edificio A",
            equipment={
                "computers": 25,
                "projector": True,
                "whiteboard": True,
                "air_conditioning": True
            }
        )
        
        classroom2 = Classroom(
            name="Aula de Informática 2",
            code="INF2",
            capacity=30,
            description="Aula de informática con equipamiento avanzado",
            location="Primera planta, edificio A",
            floor=1,
            building="Edificio A",
            equipment={
                "computers": 30,
                "projector": True,
                "whiteboard": True,
                "air_conditioning": True,
                "smart_board": True
            }
        )
        
        classroom3 = Classroom(
            name="Salón de Actos",
            code="SALON",
            capacity=100,
            description="Salón de actos para eventos y presentaciones",
            location="Planta baja, edificio principal",
            floor=0,
            building="Edificio Principal",
            equipment={
                "projector": True,
                "sound_system": True,
                "stage": True,
                "air_conditioning": True,
                "microphones": 4
            }
        )
        
        classroom4 = Classroom(
            name="Laboratorio de Física",
            code="FISICA",
            capacity=20,
            description="Laboratorio equipado para experimentos de física",
            location="Segunda planta, edificio B",
            floor=2,
            building="Edificio B",
            equipment={
                "lab_tables": 10,
                "safety_equipment": True,
                "projector": True,
                "whiteboard": True,
                "air_conditioning": True
            }
        )
        
        classroom5 = Classroom(
            name="Aula de Matemáticas",
            code="MATE1",
            capacity=35,
            description="Aula tradicional para clases de matemáticas",
            location="Primera planta, edificio A",
            floor=1,
            building="Edificio A",
            equipment={
                "whiteboard": True,
                "projector": True,
                "air_conditioning": True
            }
        )
        
        # Add classrooms to database
        db.add_all([classroom1, classroom2, classroom3, classroom4, classroom5])
        await db.commit()
        
        # Refresh objects to get IDs
        await db.refresh(admin_user)
        await db.refresh(teacher1)
        await db.refresh(teacher2)
        await db.refresh(teacher3)
        await db.refresh(classroom1)
        await db.refresh(classroom2)
        await db.refresh(classroom3)
        await db.refresh(classroom4)
        await db.refresh(classroom5)
        
        # Create sample bookings
        booking1 = Booking(
            classroom_id=classroom1.id,
            user_id=teacher1.id,
            booking_date=date.today(),
            start_time=time(8, 30),
            end_time=time(9, 25),
            subject="Programación I",
            description="Clase de introducción a la programación"
        )
        
        booking2 = Booking(
            classroom_id=classroom2.id,
            user_id=teacher2.id,
            booking_date=date.today(),
            start_time=time(10, 20),
            end_time=time(11, 15),
            subject="Matemáticas Avanzadas",
            description="Clase de cálculo diferencial"
        )
        
        booking3 = Booking(
            classroom_id=classroom4.id,
            user_id=teacher3.id,
            booking_date=date.today(),
            start_time=time(11, 45),
            end_time=time(12, 40),
            subject="Física Experimental",
            description="Práctica de laboratorio sobre mecánica"
        )
        
        # Add bookings to database
        db.add_all([booking1, booking2, booking3])
        await db.commit()
        
        print("✅ Database initialized successfully!")
        print("📊 Created:")
        print("   - 4 users (1 admin, 3 teachers)")
        print("   - 5 classrooms")
        print("   - 3 sample bookings")
        print("\n🔑 Default credentials:")
        print("   Admin: admin / admin123")
        print("   Teacher: profesor1 / profesor123")
        print("   Teacher: profesor2 / profesor123")
        print("   Teacher: profesor3 / profesor123")


if __name__ == "__main__":
    asyncio.run(init_database())

