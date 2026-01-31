-- Supabase Schema for Booking Rooms System
-- Execute this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    hashed_password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    department VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create classrooms table
CREATE TABLE IF NOT EXISTS classrooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL,
    description TEXT,
    location VARCHAR(200),
    floor INTEGER,
    building VARCHAR(100),
    equipment JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    classroom_id INTEGER NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject VARCHAR(200),
    description TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern VARCHAR(50),
    recurring_end_date DATE,
    status VARCHAR(20) DEFAULT 'confirmed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_classrooms_code ON classrooms(code);
CREATE INDEX IF NOT EXISTS idx_classrooms_active ON classrooms(is_active);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(booking_date);
CREATE INDEX IF NOT EXISTS idx_bookings_classroom_date ON bookings(classroom_id, booking_date);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classrooms_updated_at BEFORE UPDATE ON classrooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE classrooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text AND is_admin = TRUE
        )
    );

CREATE POLICY "Admins can update all users" ON users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text AND is_admin = TRUE
        )
    );

-- Create policies for classrooms table
CREATE POLICY "Anyone can view active classrooms" ON classrooms
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Admins can manage classrooms" ON classrooms
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text AND is_admin = TRUE
        )
    );

-- Create policies for bookings table
CREATE POLICY "Users can view their own bookings" ON bookings
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create their own bookings" ON bookings
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own bookings" ON bookings
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete their own bookings" ON bookings
    FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can view all bookings" ON bookings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text AND is_admin = TRUE
        )
    );

CREATE POLICY "Admins can manage all bookings" ON bookings
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text AND is_admin = TRUE
        )
    );

-- Create a function to check booking conflicts
CREATE OR REPLACE FUNCTION check_booking_conflicts(
    p_classroom_id INTEGER,
    p_booking_date DATE,
    p_start_time TIME,
    p_end_time TIME,
    p_exclude_booking_id INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM bookings
        WHERE classroom_id = p_classroom_id
        AND booking_date = p_booking_date
        AND status = 'confirmed'
        AND (p_exclude_booking_id IS NULL OR id != p_exclude_booking_id)
        AND (
            -- New booking starts during existing booking
            (start_time <= p_start_time AND end_time > p_start_time) OR
            -- New booking ends during existing booking
            (start_time < p_end_time AND end_time >= p_end_time) OR
            -- New booking completely contains existing booking
            (start_time >= p_start_time AND end_time <= p_end_time) OR
            -- Existing booking completely contains new booking
            (start_time <= p_start_time AND end_time >= p_end_time)
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to prevent booking conflicts
CREATE OR REPLACE FUNCTION prevent_booking_conflicts()
RETURNS TRIGGER AS $$
BEGIN
    IF check_booking_conflicts(
        NEW.classroom_id,
        NEW.booking_date,
        NEW.start_time,
        NEW.end_time,
        NEW.id
    ) THEN
        RAISE EXCEPTION 'Booking conflicts with existing reservation';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_booking_conflicts_trigger
    BEFORE INSERT OR UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION prevent_booking_conflicts();

-- Insert sample data
INSERT INTO users (username, email, full_name, hashed_password, is_admin, department, phone) VALUES
('admin', 'admin@instituto.edu', 'Administrador del Sistema', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Qz9z0zKz2', TRUE, 'Administración', '+34 600 000 000'),
('profesor1', 'profesor1@instituto.edu', 'María García López', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Qz9z0zKz2', FALSE, 'Informática', '+34 600 000 001'),
('profesor2', 'profesor2@instituto.edu', 'Juan Pérez Martínez', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Qz9z0zKz2', FALSE, 'Matemáticas', '+34 600 000 002'),
('profesor3', 'profesor3@instituto.edu', 'Ana Rodríguez Sánchez', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Qz9z0zKz2', FALSE, 'Física', '+34 600 000 003');

INSERT INTO classrooms (name, code, capacity, description, location, floor, building, equipment) VALUES
('Aula de Informática 1', 'INF1', 25, 'Aula equipada con ordenadores para clases de informática', 'Planta baja, edificio A', 0, 'Edificio A', '{"computers": 25, "projector": true, "whiteboard": true, "air_conditioning": true}'),
('Aula de Informática 2', 'INF2', 30, 'Aula de informática con equipamiento avanzado', 'Primera planta, edificio A', 1, 'Edificio A', '{"computers": 30, "projector": true, "whiteboard": true, "air_conditioning": true, "smart_board": true}'),
('Salón de Actos', 'SALON', 100, 'Salón de actos para eventos y presentaciones', 'Planta baja, edificio principal', 0, 'Edificio Principal', '{"projector": true, "sound_system": true, "stage": true, "air_conditioning": true, "microphones": 4}'),
('Laboratorio de Física', 'FISICA', 20, 'Laboratorio equipado para experimentos de física', 'Segunda planta, edificio B', 2, 'Edificio B', '{"lab_tables": 10, "safety_equipment": true, "projector": true, "whiteboard": true, "air_conditioning": true}'),
('Aula de Matemáticas', 'MATE1', 35, 'Aula tradicional para clases de matemáticas', 'Primera planta, edificio A', 1, 'Edificio A', '{"whiteboard": true, "projector": true, "air_conditioning": true}');

-- Note: The password hash above is for 'profesor123' - change in production!

